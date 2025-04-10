from typing import List, Dict, Union
from copy import deepcopy
from requests import request
from hashlib import sha256


class NetworkConfiguration(object):

    def __init__(self) -> None:
        # Maps match node id to match headers
        self.match_lables_map: Dict[str, Dict[str, str]] = dict()

        # Maps action node it to action list
        self.actions_map: Dict[str, List[str]] = dict()

        # Maps each flow entry node id to match node id and action node id
        self.flow_entry_map: Dict[str, Dict[str, str]] = dict()

        # Maps switch node id to a set of flow entry ids
        self.switch_to_flow_entry_map: Dict[str, set[str]] = dict()


class KGUpdateHelper:
    """
    A class to compute hash values for different data types.
    """

    def __init__(self, base_url: str = "http://localhost:8080/"):
        self.base_url: str = base_url
        self.uris: Dict[str, str] = {
            "switches": "v1.0/topology/switches",
            "flow_stats": "stats/flow/",
            "links": "v1.0/topology/links",
            "hosts": "v1.0/topology/hosts",
        }
        self.new_network_config = NetworkConfiguration()
        self.old_network_config = NetworkConfiguration()

    def __get_dpids(self, uri: str = "v1.0/topology/switches") -> List[int]:
        """
        Fetches the data of all switches in the network.
        This function sends a GET request to the specified URI and retrieves the DPID of all switches.

        Args:
            uri (str): The URI to fetch the switches.

        Returns:
            list[int]: A list of DPIDs (Data Path Identifiers) of the switches.
        """

        switch_url: str = f"{self.base_url.lstrip('/')}/{uri.lstrip('/')}"
        switches_response: list[Dict] = request("GET", switch_url).json()
        dpids: list[int] = [
            int(switch["dpid"], base=16) for switch in switches_response
        ]

        return dpids

    def update_flow_entries(self, uri: str = "stats/flow/"):
        """
        This function updates all the flow entries for all switches based on the new data from controller
        """

        flow_url: str = f"{self.base_url.lstrip('/')}/{uri.lstrip('/')}"
        dpids: List[int] = self.__get_dpids()

        # Copy current config to old network config
        self.old_network_config = deepcopy(self.new_network_config)

        # Reset new network config
        self.new_network_config.switch_to_flow_entry_map.clear()

        for dpid in dpids:
            switch_flow_url: str = f"{flow_url}{dpid}"
            flow_response: Dict = request("GET", switch_flow_url).json()
            flow_entries: List[Dict] = flow_response[str(dpid)]
            self.new_network_config.switch_to_flow_entry_map[str(dpid)] = set()

            for flow_entry in flow_entries:
                match_labels: Dict[str, Union[str, str]] = dict(
                    sorted(flow_entry["match"].items())
                )
                action_labels: List[str] = flow_entry["actions"]

                match_encode: bytes = str(match_labels).encode("utf-8")
                action_encode: bytes = str(action_labels).encode("utf-8")
                priority_encode: bytes = str(flow_entry["priority"]).encode("utf-8")
                table_id_encode: bytes = str(flow_entry["table_id"]).encode("utf-8")

                match_hash: str = sha256(match_encode).hexdigest()
                action_hash: str = sha256(action_encode).hexdigest()

                flow_hash: str = sha256(
                    priority_encode + table_id_encode + match_encode + action_encode
                ).hexdigest()

                self.new_network_config.match_lables_map[match_hash] = match_labels
                self.new_network_config.actions_map[action_hash] = action_labels
                self.new_network_config.flow_entry_map[flow_hash] = {
                    "match_id": match_hash,
                    "action_id": action_hash,
                }
                self.new_network_config.switch_to_flow_entry_map[str(dpid)].add(
                    flow_hash
                )

    def get_switches_to_remove(self) -> set[str]:
        old_switches = self.old_network_config.switch_to_flow_entry_map.keys()
        new_switches = self.new_network_config.switch_to_flow_entry_map.keys()
        return old_switches - new_switches

    def get_stale_flow_entries(
        self,
    ) -> Dict[str, set[str]]:
        """
        This function returns the flow entries that were removed from each switch

        Returns:
            Dict[str, set[str]]: dpid->set(flow_entry_id)
        """
        new_flow_entry_mappings = self.new_network_config.switch_to_flow_entry_map
        old_flow_entry_mappings = self.old_network_config.switch_to_flow_entry_map

        # Compare new and old flow enties
        stale_flow_entries: Dict[str, set[str]] = dict()
        for dpid in new_flow_entry_mappings.keys():
            if dpid not in old_flow_entry_mappings:
                continue
            stale_flow_entries[dpid] = (
                old_flow_entry_mappings[dpid] - new_flow_entry_mappings[dpid]
            )

        return stale_flow_entries

    def get_new_flow_entries(
        self,
    ) -> Dict[str, set[str]]:
        """
        This function returns flow entries that were added in each switch

        Returns:
            Dict[str, set[str]]: dpid->set(flow_entry_id)
        """
        new_flow_entry_mappings = self.new_network_config.switch_to_flow_entry_map
        old_flow_entry_mappings = self.old_network_config.switch_to_flow_entry_map

        # Compare new and old flow enties
        new_flow_entries: Dict[str, set[str]] = dict()
        for dpid in new_flow_entry_mappings.keys():
            # For new switch there will be no stale entries
            if dpid not in old_flow_entry_mappings:
                new_flow_entries[dpid] = new_flow_entry_mappings[dpid]
                continue

            new_flow_entries[dpid] = (
                new_flow_entry_mappings[dpid] - old_flow_entry_mappings[dpid]
            )

        return new_flow_entries


# from pprint import pprint
#
# if __name__ == "__main__":
#     HC = Hashcompute()
#     ch = 32
#
#     while True:
#         ch = ord(input("Press space to continue: "))
#         if ch == 32:
#             flow_remove = HC.get_stale_and_new_relations()
#             pprint(flow_remove)
