from typing import List, Dict, Tuple, Union
from copy import deepcopy
from requests import request
from hashlib import sha256
import json

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
            "hosts": "v1.0/topology/hosts"
        }
        self.matchs_hash_dict : Dict[str, Dict[str, str]] = dict()
        self.actions_hash_dict : Dict[str, List[str]] = dict()
        self.switch_hash_dict : Dict[str,Dict[str, str]] = dict()
        self.database: List[Dict] = (dict(), dict(), dict())


    def get_dpids(self, uri : str ="v1.0/topology/switches") -> List[int]:
        """
        Fetches the data of all switches in the network.
        This function sends a GET request to the specified URI and retrieves the DPID of all switches.

        Args:
            uri (str): The URI to fetch the switches.

        Returns:
            list[int]: A list of DPIDs (Data Path Identifiers) of the switches.
        """

        switch_url : str = f"{self.base_url.lstrip('/')}/{uri.lstrip('/')}"
        switches_response : list[Dict] = request("GET", switch_url).json()
        dpids:list[int] = [int(switch['dpid'], base=16) for switch in switches_response]

        return dpids


    def get_flow_match_action(self, uri: str = "stats/flow/") -> Tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, str]], Dict[str, List[str]]]:
        """
        Fetches the flow rules for a specific switch identified by its DPID.

        Args:
            uri (str): The URI to fetch the flow rules.

        Returns:
            Tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, str]], Dict[str, List[str]]]: A tuple containing three dictionaries:
                - switch_hash_dict: A dictionary of flow hashes for each switch.
                - matchs_hash_dict: A dictionary of match hashes.
                - actions_hash_dict: A dictionary of action hashes.
        """

        flow_url: str = f"{self.base_url.lstrip('/')}/{uri.lstrip('/')}"
        dpids: List[int] = self.get_dpids()

        for dpid in dpids:
            switch_flow_url: str = f"{flow_url}{dpid}"
            flow_response: Dict = request("GET", switch_flow_url).json()
            flow_entries : List[Dict] = flow_response[str(dpid)]
            flow_hash_dict: Dict[str, Dict[str, str]] = dict()
            
            for flow_entry in flow_entries:

                match_labels: Dict[str, Union[str, int]] = dict(sorted(flow_entry['match'].items()))
                action_labels: List[str] = flow_entry['actions']

                match_encode:bytes = str(match_labels).encode('utf-8')
                action_encode:bytes = str(action_labels).encode('utf-8')
                priority_encode:bytes = str(flow_entry['priority']).encode('utf-8')
                table_id_encode:bytes = str(flow_entry['table_id']).encode('utf-8')

                match_hash: str = sha256(match_encode).hexdigest()
                action_hash: str = sha256(action_encode).hexdigest()

                flow_hash: str = sha256(priority_encode + table_id_encode + match_encode + action_encode).hexdigest()
                
                self.matchs_hash_dict[match_hash] = match_labels
                self.actions_hash_dict[action_hash] = action_labels
                flow_hash_dict[flow_hash] = {
                    "match": match_hash,
                    "actions": action_hash
                }
            
            self.switch_hash_dict[str(dpid)] = flow_hash_dict

        return (self.switch_hash_dict , self.matchs_hash_dict, self.actions_hash_dict)


    def compare(self) -> Dict[str, Dict[str, str]]:
        """
        Compares the current flow rules with the previous ones and returns the differences.
        This function computes the hashes of the current flow rules and compares them with the previously stored hashes.
        If there are any differences, it updates the database with the new hashes.
        It returns a dictionary containing the flow entries that need to be removed.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary containing the flow entries that need to be removed.
        """

        new_hashes = self.get_flow_match_action()

        switch_hashes, _, _ = new_hashes
        old_switch_hashes, _, _ = self.database
        flow_entry_remove: Dict[str, Dict[str, str]] = dict()

        for dpid in switch_hashes.keys():

            if old_switch_hashes.get(dpid):
                for flow_hash in switch_hashes[dpid].keys():
                    if old_switch_hashes[dpid].get(flow_hash):
                        old_switch_hashes[dpid].pop(flow_hash)

            flow_entry_remove.update(old_switch_hashes)
        
        self.database = deepcopy(new_hashes)

        return flow_entry_remove


if __name__ == "__main__":
    HC = Hashcompute()
    dpids: List[int] = HC.get_dpids()
    print(dpids)

    HC.compare()
