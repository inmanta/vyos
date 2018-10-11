"""
    Vyos interface module

    :copyright: 2018 Inmanta
    :contact: code@inmanta.com
    :license: Inmanta EULA
"""
import re

from inmanta.resources import resource, PurgeableResource, Resource
from inmanta.agent.handler import provider, CRUDHandler, HandlerContext, cache, ResourcePurged, SkipResource

import vymgmt
import vyattaconfparser
import pexpect

@resource("vyos::Config", id_attribute="nodeid", agent="device")
class Config(PurgeableResource):
    fields = ("node", "config", "credential", "never_delete", "save", "keys_only", "ignore_keys", "device")

    @staticmethod
    def get_credential(_, obj):
        obj = obj.credential
        return {"user": obj.user, "password": obj.password, "port": obj.port,
                "address": obj.address}

    @staticmethod
    def get_nodeid(_, obj):
        return obj.node.replace(" ", "_")

    @staticmethod
    def get_config(_, obj):
        config = str(obj.config)
        for ext in obj.extra:
            config += "\n" + ext.config

        return config


@provider("vyos::Config", name="sshconfig")
class VyosHandler(CRUDHandler):
    def __init__(self, agent, io=None):
        CRUDHandler.__init__(self, agent, io)
        self.__cache = {}

    #@cache(for_version=True)
    def get_connection(self, version, resource):
        cred = resource.credential
        vyos = vymgmt.Router(cred["address"], cred["user"], cred["password"], cred["port"])
        try:
            vyos.login()
        except pexpect.pxssh.ExceptionPxssh:
            raise SkipResource("Host not available (yet)")
        return vyos

    def pre(self, ctx: HandlerContext, resource: Config) -> None:
        vyos = self.get_connection(resource.id.version, resource)
        status = vyos._status()
        if not status["logged_in"]:
            try:
                vyos.login()
            except pexpect.pxssh.ExceptionPxssh:
                raise SkipResource("Host not available (yet)")

    def post(self, ctx: HandlerContext, resource: Config) -> None:
        vyos = self.get_connection(resource.id.version, resource)
        vyos.logout()

    def get_config_dict(self, ctx, resource, vyos):
        if resource.device in self.__cache:
            ctx.debug("Get raw config from cache")
            return self.__cache[resource.device]

        config = vyos.run_op_mode_command("echo 'START PRINT'; cat /config/config.boot; echo 'END PRINT'")
        config = config.replace("\r", "")
        match = re.search(r"[^\n]+\nSTART PRINT\n(.*)END PRINT\n", config, re.DOTALL)
        if match:
            ctx.debug("Got raw config", config=match.group(1))
            conf_dict = vyattaconfparser.parse_conf(match.group(1))
            self.__cache[resource.device] = conf_dict
            return conf_dict

    def _invalidate_cache(self, resource):
        if resource.device in self.__cache:
            del self.__cache[resource.device + "_" + resource.id.version]

    def _dict_to_path(self, node, dct):
        paths = []
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
            return old[k] != new [k]

        def get_old_value(k):
            if k not in old:
                return None
            return old[k]

        def get_new_value(k):
            if k not in new:
                return None
            value = new[k]
            return value

        changed = {k:{"current": get_old_value(k), "desired":get_new_value(k)} for k in allkeys if is_diff(k)}

        return changed

    def _diff(self, current, desired):
        """
            Generate a similar tree
        """
        dcfg = {}

        for line in desired.config.split("\n"):
            parts = line.split(" ")
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
            if key not in current.ignore_keys and (len(current.keys_only) == 0 or key in current.keys_only):
                if key in ccfg:
                    if isinstance(ccfg[key], str):
                        ccfg[key] = [ccfg[key], value]
                    else:
                        ccfg[key].append(value)
                else:
                    ccfg[key] = value

        changed = self._dict_diff(False, ccfg, dcfg)

        return changed

    def _execute(self, ctx: HandlerContext, resource: Config, delete: bool) -> None:
        commands = [x for x in resource.config.split("\n") if len(x) > 0]
        vyos = self.get_connection(resource.id.version, resource)
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

    def read_resource(self, ctx: HandlerContext, resource: Config) -> None:
        vyos = self.get_connection(resource.id.version, resource)
        current = self.get_config_dict(ctx, resource, vyos)
        keys = resource.node.split(" ")

        cfg = current
        for key in resource.node.split(" "):
            if isinstance(cfg, str):
                pass
            elif key in cfg:
                cfg = cfg[key]
            else:
                raise ResourcePurged()

        ctx.debug("Comparing desired with current", desired=resource.config, current=cfg, node=resource.node, raw_current=current)

        current_cfg = self._dict_to_path(resource.node, cfg)
        ctx.debug("Current paths", path=current_cfg)
        resource.config = current_cfg

    def create_resource(self, ctx: HandlerContext, resource: Config) -> None:
        ctx.debug("Creating resource, invalidating cache")
        if resource.device in self.__cache:
            del self.__cache[resource.device]

        self._execute(ctx, resource, delete=False)
        ctx.set_created()

    def delete_resource(self, ctx: HandlerContext, resource: Config) -> None:
        ctx.debug("Deleting resource, invalidating cache")
        if resource.device in self.__cache:
            del self.__cache[resource.device]

        vyos = self.get_connection(resource.id.version, resource)
        vyos.configure()
        vyos.delete(resource.node)
        vyos.commit()
        if resource.save:
            vyos.save()
        vyos.exit(force=True)
        ctx.set_purged()

    def update_resource(self, ctx: HandlerContext, changes: dict, resource: Config) -> None:
        ctx.debug("Updating resource, invalidating cache")
        if resource.device in self.__cache:
            del self.__cache[resource.device]

        self._execute(ctx, resource, delete=True)
        ctx.set_updated()