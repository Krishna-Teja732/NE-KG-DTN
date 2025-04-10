from utils.kg_update_helper import KGUpdateHelper
from utils.graph_db_helper import DatabaseHelper


class KGBuild:

    def __init__(self) -> None:
        self.dbHelper = DatabaseHelper()
        self.updateHelper = KGUpdateHelper()

    def start(self):
        update = "y"
        while update == "" or update == "y":
            print("Updating KG")
            self.updateHelper.update_flow_entries()

            self.__remove_old_switches()

            self.__add_new_flow_entries()

            self.__remove_old_flow_entries()
            print("KG Update complete\n")

            update = input("Start next update iteration(Y/n): ").strip().lower()

    def __remove_old_switches(self):
        for dpid in self.updateHelper.get_switches_to_remove():
            self.dbHelper.delete_switch(dpid)

    def __add_new_flow_entries(self):
        new_relations = self.updateHelper.get_new_flow_entries()

        for dpid, flow_entries in new_relations.items():
            for flow_entry_id in flow_entries:
                match_id = self.updateHelper.new_network_config.flow_entry_map[
                    flow_entry_id
                ]["match_id"]
                action_id = self.updateHelper.new_network_config.flow_entry_map[
                    flow_entry_id
                ]["action_id"]
                self.dbHelper.create_flow_entry(flow_entry_id, match_id, action_id)
                self.dbHelper.add_flow_entry_to_switch(dpid, flow_entry_id)

    def __remove_old_flow_entries(self):
        stale_relations = self.updateHelper.get_stale_flow_entries()
        for dpid, flow_entries in stale_relations.items():
            for flow_entry_id in flow_entries:
                self.dbHelper.delete_flow_entry_from_switch(dpid, flow_entry_id)


if __name__ == "__main__":
    builder = KGBuild()
    builder.start()
