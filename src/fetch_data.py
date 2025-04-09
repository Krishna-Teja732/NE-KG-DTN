from typing import List, Dict, Tuple, Union
from copy import deepcopy
from requests import request
from hashlib import sha256


class Hashcompute:
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
        # Maps match node id to match headers
        self.match_lables_map: Dict[str, Dict[str, str]] = dict()

        # Maps action node it to action list
        self.actions_map: Dict[str, List[str]] = dict()

        # Maps each flow entry node id to match node id and action node id
        self.flow_entry_map: Dict[str, Dict[str, str]] = dict()

        # Maps switch node id to a set of flow entry ids
        self.switch_to_flow_entry_map: Dict[str, set[str]] = dict()

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

    def __update_flow_entries(self, uri: str = "stats/flow/"):
        """
        This function updates all the flow entries for all switches based on the new data from controller
        """

        flow_url: str = f"{self.base_url.lstrip('/')}/{uri.lstrip('/')}"
        dpids: List[int] = self.__get_dpids()

        for dpid in dpids:
            switch_flow_url: str = f"{flow_url}{dpid}"
            flow_response: Dict = request("GET", switch_flow_url).json()
            flow_entries: List[Dict] = flow_response[str(dpid)]
            self.switch_to_flow_entry_map[str(dpid)] = set()

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

                self.match_lables_map[match_hash] = match_labels
                self.actions_map[action_hash] = action_labels
                self.flow_entry_map[flow_hash] = {
                    "match": match_hash,
                    "actions": action_hash,
                }
                self.switch_to_flow_entry_map[str(dpid)].add(flow_hash)

    def get_stale_and_new_relations(
        self,
    ) -> Tuple[Dict[str, set[str]], Dict[str, set[str]]]:
        """
        This function returns
        1. Flow rules are removed from the switch
        2. Flow rules added to the switch

        Returns:
            Tuple[Dict[str, set[str]], Dict[str, set[str]]]: index 0 -> flow entries removed, index 1 -> flow entries added
        """

        # Copy old flow entry mappings
        old_flow_entry_mappings: Dict[str, set[str]] = deepcopy(
            self.switch_to_flow_entry_map
        )

        # Update to flow entry mappings
        self.__update_flow_entries()
        new_flow_entry_mappings = self.switch_to_flow_entry_map

        # Compare new and old flow enties
        stale_flow_enties = dict()
        new_flow_enties = dict()

        for dpid in new_flow_entry_mappings.keys():

            if dpid not in old_flow_entry_mappings:
                old_flow_entry_mappings[dpid] = set()

            stale_flow_enties[dpid] = (
                old_flow_entry_mappings[dpid] - new_flow_entry_mappings[dpid]
            )

            new_flow_enties[dpid] = (
                new_flow_entry_mappings[dpid] - old_flow_entry_mappings[dpid]
            )

        return stale_flow_enties, new_flow_enties


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
