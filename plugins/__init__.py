import re

from inmanta.resources import resource, PurgeableResource, Resource
from inmanta.agent.handler import provider, CRUDHandler, HandlerContext, cache, ResourcePurged, SkipResource

import vymgmt
import vyattaconfparser
import pexpect

@resource("vyos::Config", id_attribute="nodeid", agent="device")
class Config(PurgeableResource):
    fields = ("node", "config", "credential", "never_delete", "save")

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

    def get_config_dict(self, ctx, vyos):
        config = vyos.run_op_mode_command("echo 'START PRINT'; cat /config/config.boot; echo 'END PRINT'")
        config = config.replace("\r", "")
        match = re.search(r"[^\n]+\nSTART PRINT\n(.*)END PRINT\n", config, re.DOTALL)
        if match:
            ctx.debug("Got raw config", config=match.group(1))
            conf_dict = vyattaconfparser.parse_conf(match.group(1))
            return conf_dict

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
        cfg = self.get_config_dict(ctx, vyos)
        keys = resource.node.split(" ")
        ctx.debug("Comparing desired with current", desired=resource.config, current=cfg, node=resource.node)


        for key in resource.node.split(" "):
            if isinstance(cfg, str):
                pass
            elif key in cfg:
                cfg = cfg[key]
            else:
                raise ResourcePurged()

        resource.config = ""

    def create_resource(self, ctx: HandlerContext, resource: Config) -> None:
        self._execute(ctx, resource, delete=False)
        ctx.set_created()

    def delete_resource(self, ctx: HandlerContext, resource: Config) -> None:
        vyos = self.get_connection(resource.id.version, resource)
        vyos.configure()
        vyos.delete(resource.node)
        vyos.commit()
        if resource.save:
            vyos.save()
        vyos.exit(force=True)
        ctx.set_purged()

    def update_resource(self, ctx: HandlerContext, changes: dict, resource: Config) -> None:
        self._execute(ctx, resource, delete=True)
        ctx.set_updated()