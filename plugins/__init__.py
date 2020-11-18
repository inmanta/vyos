"""
    Vyos interface module

    :copyright: 2018 Inmanta
    :contact: code@inmanta.com
    :license: Inmanta EULA
"""
import itertools
import re
from functools import reduce
from typing import Any, Tuple

import pexpect
import vyattaconfparser
import vymgmt
from inmanta.agent.handler import (
    CRUDHandler,
    HandlerContext,
    ResourcePurged,
    SkipResource,
    cache,
    provider,
)
from inmanta.resources import PurgeableResource, resource
from pexpect import pxssh
from pexpect.exceptions import TIMEOUT


@resource("vyos::Config", id_attribute="nodeid", agent="device")
class Config(PurgeableResource):
    fields = (
        "node",
        "config",
        "credential",
        "never_delete",
        "save",
        "keys_only",
        "ignore_keys",
        "device",
        "facts",
        "skip_on_connect_error",
    )

    @staticmethod
    def get_credential(_, obj):
        obj = obj.credential
        return {
            "user": obj.user,
            "password": obj.password,
            "port": obj.port,
            "address": obj.address,
        }

    @staticmethod
    def get_nodeid(_, obj):
        return obj.node.replace(" ", "_")

    @staticmethod
    def get_config(_, obj):
        def get_config_recur(instance: Any) -> str:
            return reduce(
                lambda acc, extra: acc + "\n" + get_config_recur(extra),
                instance.extra,
                str(instance.config),
            )

        # strip out all empty lines
        lines = []
        for line in get_config_recur(obj).split("\n"):
            line = line.strip()
            if line:
                lines.append(line)

        return "\n".join(lines)


@resource("vyos::vpn::KeyGen", id_attribute="id", agent="device")
class KeyGen(PurgeableResource):
    fields = ("credential", "skip_on_connect_error")

    @staticmethod
    def get_credential(_, obj):
        obj = obj.credential
        return {
            "user": obj.user,
            "password": obj.password,
            "port": obj.port,
            "address": obj.address,
        }

    @staticmethod
    def get_skip_on_connect_error(_, obj):
        return obj.host.skip_on_connect_error


@resource("vyos::IpFact", id_attribute="id", agent="device")
class IpFact(PurgeableResource):
    fields = ("credential", "interface", "skip_on_connect_error")

    @staticmethod
    def get_interface(_, obj):
        return obj.interface.name

    @staticmethod
    def get_credential(_, obj):
        obj = obj.credential
        return {
            "user": obj.user,
            "password": obj.password,
            "port": obj.port,
            "address": obj.address,
        }

    @staticmethod
    def get_skip_on_connect_error(_, obj):
        return obj.host.skip_on_connect_error


class Router(vymgmt.Router):
    def login(self):
        self.__conn = pxssh.pxssh()
        self.__conn.login(
            self.__address,
            self.__user,
            password=self.__password,
            port=self.__port,
            sync_original_prompt=False,
        )
        self.__logged_in = True


class VyosBaseHandler(CRUDHandler):
    def __init__(self, agent, io=None):
        CRUDHandler.__init__(self, agent, io)
        self.connection = None

    def get_connection(self, ctx, version, resource):
        if self.connection:
            return self.connection

        cred = resource.credential
        vyos = Router(cred["address"], cred["user"], cred["password"], cred["port"])
        try:
            vyos.login()
            # prevent bugs where it is reported that
            # terminal is not fully functional
            vyos.run_op_mode_command("export TERM=ansi")
        except pexpect.pxssh.ExceptionPxssh:
            ctx.exception(
                "Failed to connect to host %(address)s", address=cred["address"]
            )
            if resource.skip_on_connect_error:
                raise SkipResource(
                    "Host not available (yet). Skipping because skip_on_connect_error == true"
                )
            raise
        self.connection = vyos
        return vyos

    def post(self, ctx: HandlerContext, resource: Config) -> None:
        if self.connection:
            try:
                # Vyos cannot logout before exiting configuration mode
                self.connection.exit(force=True)
                self.connection.logout()
                self.connection = None
            except:  # noqa: E722
                ctx.exception("Failed to close connection")

    def _execute_command(
        self, ctx: HandlerContext, vyos, command, terminator, timeout=10
    ):
        """Patch for wonky behavior of vymgmt, after exit it can no longer use the unique prompt"""
        conn = vyos._Router__conn

        conn.sendline(command)

        i = conn.expect([terminator, TIMEOUT], timeout=timeout)

        output = conn.before

        if isinstance(output, bytes):
            output = output.decode("utf-8")

        if not i == 0:
            ctx.debug(
                "got raw result %(result)s", result=conn.before.decode(), cmd=command
            )
            raise vymgmt.VyOSError("Connection timed out")

        if not conn.prompt():
            ctx.debug(
                "got raw result %(result)s", result=conn.before.decode(), cmd=command
            )
            raise vymgmt.VyOSError("Connection timed out")

        return output


@provider("vyos::Config", name="sshconfig")
class VyosHandler(VyosBaseHandler):
    @cache(timeout=60, for_version=True)
    def get_versioned_cache(self, version):
        # rely on built in cache mechanism to clean up
        return {}

    def get_config_dict(self, ctx, resource, vyos):
        cache = self.get_versioned_cache(resource.id.version)
        if resource.device in cache:
            ctx.debug("Get raw config from cache")
            return cache[resource.device]
        out = vyos.configure()
        out = vyos.run_conf_mode_command("save /tmp/inmanta_tmp")
        if not (
            "Saving configuration to '/tmp/inmanta_tmp'" in out
            or "saving configuration to non-default location '/tmp/inmanta_tmp'" in out
        ):
            raise SkipResource(f"Could not save config: {out}")
        ctx.debug("Saved config: %(out)s", out=out)
        out = vyos.exit()

        # vyos.configure() breaks unique prompt, causing config transfer to fail
        command = "cat /tmp/inmanta_tmp; echo 'END PRINT'"
        config = self._execute_command(ctx, vyos, command, "END PRINT\r\n")
        config = config.replace("\r", "")
        config = config.replace(command, "")
        ctx.debug("Got raw config", config=config)
        conf_dict = vyattaconfparser.parse_conf(config)
        cache[resource.device] = conf_dict
        return conf_dict

    def _invalidate_cache(self, resource):
        cache = self.get_versioned_cache(resource.id.version)
        if resource.device in cache:
            del cache[resource.device]

    def _dict_to_path(self, node, dct):
        paths = []

        if dct is None:
            return paths

        if isinstance(dct, str):
            paths.append((node, dct))
            return paths

        for k, v in dct.items():
            if isinstance(v, str):
                paths.append((node + " " + k, v))
            elif isinstance(v, dict) and len(v) == 0:
                paths.append((node, k))
            else:
                paths.extend(self._dict_to_path(node + " " + k, v))

        return paths

    def _dict_diff(self, ignore, old, new):
        old_keys = old.keys()
        new_keys = new.keys()

        allkeys = old_keys | new_keys

        def is_diff(k):
            if k not in old:
                return True
            if k not in new:
                return not ignore
            if new[k] is None:
                return False
            return old[k] != new[k]

        def get_old_value(k):
            if k not in old:
                return None
            return old[k]

        def get_new_value(k):
            if k not in new:
                return None
            value = new[k]
            return value

        changed = {
            k: {"current": get_old_value(k), "desired": get_new_value(k)}
            for k in allkeys
            if is_diff(k)
        }

        return changed

    def _diff(self, current, desired):
        """
        Generate a similar tree
        """
        dcfg = {}

        for line in desired.config.strip().split("\n"):
            parts = line.strip().split(" ")
            if line != current.node and len(line.strip()) > 0:
                key = " ".join(parts[:-1])
                value = parts[-1]
                if key in dcfg:
                    if isinstance(dcfg[key], str):
                        dcfg[key] = [dcfg[key], value]
                    else:
                        dcfg[key].append(value)
                else:
                    dcfg[key] = value

        ccfg = {}
        for key, value in current.config:
            if key not in current.ignore_keys and (
                len(current.keys_only) == 0 or key in current.keys_only
            ):
                if key in ccfg:
                    if isinstance(ccfg[key], str):
                        ccfg[key] = [ccfg[key], value]
                    else:
                        ccfg[key].append(value)
                else:
                    ccfg[key] = value

        if ccfg and desired.purged:
            changed = {"purged": dict(desired=desired.purged, current=False)}
        else:
            changed = self._dict_diff(False, ccfg, dcfg)

        return changed

    def _execute(self, ctx: HandlerContext, resource: Config, delete: bool) -> None:
        commands = [x for x in resource.config.split("\n") if len(x) > 0]
        vyos = self.get_connection(ctx, resource.id.version, resource)
        try:
            vyos.configure()
            if delete and not resource.never_delete:
                ctx.debug("Deleting %(node)s", node=resource.node)
                vyos.delete(resource.node)

            for cmd in commands:
                ctx.debug("Setting %(cmd)s", cmd=cmd)
                if delete and resource.never_delete:
                    try:
                        vyos.delete(cmd)
                    except vymgmt.ConfigError:
                        pass
                vyos.set(cmd)

            vyos.commit()
            if resource.save:
                vyos.save()
            vyos.exit(force=True)
        except vymgmt.router.VyOSError:
            ctx.debug(
                "got raw raw result %(result)s",
                result=vyos._Router__conn.before.decode("utf-8"),
                cmd=cmd,
            )
            raise

    def read_resource(self, ctx: HandlerContext, resource: Config) -> None:
        if resource.facts:
            return
        vyos = self.get_connection(ctx, resource.id.version, resource)
        current = self.get_config_dict(ctx, resource, vyos)

        cfg = current
        for key in resource.node.split(" "):
            if isinstance(cfg, str):
                cfg = {cfg: {}}
                break
            elif key in cfg:
                cfg = cfg[key]
            else:
                raise ResourcePurged()

        ctx.debug(
            "Comparing desired with current",
            desired=resource.config,
            current=cfg,
            node=resource.node,
            raw_current=current,
        )

        current_cfg = self._dict_to_path(resource.node, cfg)
        ctx.debug("Current paths", path=current_cfg)
        resource.config = current_cfg

    def create_resource(self, ctx: HandlerContext, resource: Config) -> None:
        if resource.facts:
            return
        ctx.debug("Creating resource, invalidating cache")
        self._invalidate_cache(resource)

        self._execute(ctx, resource, delete=False)
        ctx.set_created()

    def delete_resource(self, ctx: HandlerContext, resource: Config) -> None:
        if resource.facts:
            return
        ctx.debug("Deleting resource, invalidating cache")
        self._invalidate_cache(resource)

        vyos = self.get_connection(ctx, resource.id.version, resource)
        vyos.configure()
        vyos.delete(resource.node)
        vyos.commit()
        if resource.save:
            vyos.save()
        vyos.exit(force=True)
        ctx.set_purged()

    def update_resource(
        self, ctx: HandlerContext, changes: dict, resource: Config
    ) -> None:
        if resource.facts:
            return
        ctx.debug("Updating resource, invalidating cache")
        self._invalidate_cache(resource)

        self._execute(ctx, resource, delete=True)
        ctx.set_updated()

    def facts(self, ctx: HandlerContext, resource: Config) -> None:
        vyos = self.get_connection(ctx, resource.id.version, resource)
        orig = current = self.get_config_dict(ctx, resource, vyos)
        path = resource.node.split(" ")
        for el in path:
            if el in current:
                current = current[el]
            else:
                ctx.debug("No value found", error=current, path=path, orig=orig)
                return {}
        return {"value": current}


@provider("vyos::vpn::KeyGen", name="keygen")
class KeyGenHandler(VyosBaseHandler):
    def get_pubkey(self, ctx: HandlerContext, resource: Config) -> str:
        vyos = self.get_connection(ctx, resource.id.version, resource)
        cmd = "TERM=ansi show vpn ike rsa-keys"
        try:
            result = re.sub(
                "\x1b\\[[0-9]?[a-zA-Z]",
                "",
                vyos.run_op_mode_command(cmd).replace("\r", ""),
            )
        except vymgmt.router.VyOSError:
            ctx.debug(
                "got raw raw result %(result)s",
                result=vyos._Router__conn.before.decode("utf-8"),
                cmd=cmd,
            )
            raise
        ctx.debug("got raw result %(result)s", result=result, cmd=cmd)

        marker = "Local public key (/config/ipsec.d/rsa-keys/localhost.key):"

        if marker in result:
            idx = result.find(marker)
            result = result[idx + len(marker) :]
            if "====" in result:
                idx = result.find("====")
                result = result[:idx]
            ctx.debug("got result %(result)s", result=result, cmd=cmd)
            result = result.strip()
        else:
            raise ResourcePurged()
        return result

    def read_resource(self, ctx: HandlerContext, resource: Config) -> None:
        self.get_pubkey(ctx, resource)

    def create_resource(self, ctx: HandlerContext, resource: Config) -> None:
        vyos = self.get_connection(ctx, resource.id.version, resource)

        # try old command first, new one hangs due to insufficient entropy
        cmd = "generate vpn rsa-key bits 2048 random /dev/urandom"
        result = vyos.run_op_mode_command(cmd)
        if "Invalid command:" in result:
            cmd = "generate vpn rsa-key bits 2048"
            result = vyos.run_op_mode_command(cmd)

        ctx.debug("got result %(result)s", result=result, cmd=cmd)

        assert "has been generated" in result

    def facts(self, ctx: HandlerContext, resource: Config) -> None:
        try:
            pubkey = self.get_pubkey(ctx, resource)
            return {"key": pubkey}
        finally:
            self.post(ctx, resource)


@provider("vyos::IpFact", name="IpFact")
class IpFactHandler(VyosBaseHandler):
    def parse_line(self, line: str) -> Tuple[str, str]:
        parts = re.split(" +", line)
        if len(parts) < 2:
            return None
        if parts[1] == "-":
            return None
        else:
            return (
                parts[0].replace("\x1b[m", "").strip(),
                parts[1].replace("\x1b[m", "").strip(),
            )

    def facts(self, ctx: HandlerContext, resource: IpFact) -> None:
        # example output
        # vyos@vyos:~$ show interfaces
        # Codes: S - State, L - Link, u - Up, D - Down, A - Admin Down
        # Interface        IP Address                        S/L  Description
        # ---------        ----------                        ---  -----------
        # eth0             10.0.0.7/24                       u/u
        # eth1             10.1.0.15/24                      u/u
        # lo               127.0.0.1/8                       u/u
        #                  ::1/128
        try:

            vyos = self.get_connection(ctx, resource.id.version, resource)
            cmd = "show interfaces"
            interface = resource.interface
            result = vyos.run_op_mode_command(cmd).replace("\r", "")
            ctx.debug("got result %(result)s", result=result, cmd=cmd)

            parsed_lines = [self.parse_line(line) for line in result.split("\n")]
            parsed_lines = [line for line in parsed_lines if line is not None]

            # find right lines
            ips = itertools.dropwhile(lambda x: x[0] != interface, parsed_lines)
            ips = list(
                itertools.takewhile(lambda x: x[0] == interface or not x[0], ips)
            )

            ctx.debug("got ips %(ips)s", ips=ips)

            ips = [ip[1] for ip in ips]

            if not ips:
                return {}

            if len(ips) == 1:
                return {"ip_address": ips[0]}
            else:
                ips = sorted(ips)
                out = {"ip_address": ips[0]}
                for i, addr in enumerate(ips):
                    out[f"ip_address_{i}"] = addr
                return out
        finally:
            self.post(ctx, resource)
