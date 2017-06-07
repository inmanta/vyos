import re

from inmanta.resources import resource, PurgeableResource, Resource
from inmanta.agent.handler import provider, CRUDHandler, HandlerContext, cache, ResourcePurged

import vymgmt
import vyattaconfparser

@resource("vyos::Config", id_attribute="nodeid", agent="device")
class Config(PurgeableResource):
    fields = ("node", "config", "credential")

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
    @cache(for_version=True)
    def get_connection(self, version, resource):
        cred = resource.credential
        vyos = vymgmt.Router(cred["address"], cred["user"], cred["password"], cred["port"])
        try:
            vyos.login()
        except Exception as e:
            import traceback
            traceback.print_exc()
        return vyos

    def post(self, ctx: HandlerContext, resource: Config) -> None:
        vyos = self.get_connection(resource.id.version, resource)
        vyos.logout()

    def get_config_dict(self, vyos):
        config = vyos.run_op_mode_command("echo 'START PRINT'; cat /config/config.boot; echo 'END PRINT'")
        config = config.replace("\r", "")
        match = re.search(r"[^\n]+\nSTART PRINT\n(.*)END PRINT\n", config, re.DOTALL)
        if match:
            conf_dict = vyattaconfparser.parse_conf(match.group(1))
            return conf_dict

    def check_resource(self, ctx: HandlerContext, resource: Resource) -> Resource:
        current = resource.clone()
        vyos = self.get_connection(resource.id.version, resource)
        cfg = self.get_config_dict(vyos)

        for key in resource.node.split(" "):
            if key in cfg:
                cfg = cfg[key]
            else:
                print("Purged!!")
        return current

    def _execute(self, ctx: HandlerContext, resource: Config, delete: bool) -> None:
        commands = [x for x in resource.config.split("\n") if len(x) > 0]
        vyos = self.get_connection(resource.id.version, resource)
        vyos.configure()
        if delete:
            vyos.delete(resource.node)
    
        for cmd in commands:
            vyos.set(cmd)
    
        vyos.commit()
        vyos.save()
        vyos.exit()

    def read_resource(self, ctx: HandlerContext, resource: Config) -> None:
        current = resource.clone()
        vyos = self.get_connection(resource.id.version, resource)
        cfg = self.get_config_dict(vyos)

        for key in resource.node.split(" "):
            if key in cfg:
                cfg = cfg[key]
            else:
                raise ResourcePurged()
        return current

    def create_resource(self, ctx: HandlerContext, resource: Config) -> None:
        self._execute(ctx, resource, delete=False)

    def delete_resource(self, ctx: HandlerContext, resource: Config) -> None:
        vyos = self.get_connection(resource.id.version, resource)
        vyos.configure()
        vyos.delete(resource.node)
        vyos.commit()
        vyos.save()
        vyos.exit()

    def update_resource(self, ctx: HandlerContext, changes: dict, resource: Config) -> None:
        self._execute(ctx, resource, delete=True)
