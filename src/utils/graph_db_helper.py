from neo4j import GraphDatabase, Transaction


class DatabaseHelper:

    def __init__(self) -> None:
        URI = "neo4j:7687"
        AUTH = ("neo4j", "defaultGraphDB")
        self.driver = GraphDatabase.driver(URI, auth=AUTH)
        self.db_session = self.driver.session()

    def add_flow_entry_to_switch(self, dpid, flow_entry_id):
        self.db_session.execute_write(
            GraphQueries.add_flow_entry_to_switch, dpid, flow_entry_id
        )

    def create_flow_entry(self, flow_entry_id, match_id, action_id):
        self.db_session.execute_write(
            GraphQueries.add_match_to_flow_entry, flow_entry_id, match_id
        )
        self.db_session.execute_write(
            GraphQueries.add_action_to_flow_entry, flow_entry_id, action_id
        )

    def delete_flow_entry_from_switch(self, dpid, flow_entry_id):
        self.db_session.execute_write(
            GraphQueries.delete_flow_entry_from_switch, dpid, flow_entry_id
        )

    def delete_switch(self, dpid):
        self.db_session.execute_write(GraphQueries.delete_switch, dpid)


class GraphQueries:
    @staticmethod
    def add_flow_entry_to_switch(tx: Transaction, dpid, flow_entry_id):
        CREATE_HAS_ENTRY_RELATION = """
        MERGE (switch:OpenFlowSwitch {dpid:$dpid})
        MERGE (entry:FlowEntry {flow_entry_id: $flow_entry_id}) 
        MERGE (switch)-[:hasFlowEntry]->(entry)
        """
        tx.run(CREATE_HAS_ENTRY_RELATION, dpid=dpid, flow_entry_id=flow_entry_id)

    @staticmethod
    def add_match_to_flow_entry(tx: Transaction, flow_entry_id, match_id):
        CREATE_HAS_MATCH_RELATION = """
        MERGE (entry:FlowEntry {flow_entry_id: $flow_entry_id})
        MERGE (match:Match {match_id: $match_id})
        MERGE (entry)-[:hasMatch]->(match)
        """
        tx.run(
            CREATE_HAS_MATCH_RELATION, flow_entry_id=flow_entry_id, match_id=match_id
        )

    @staticmethod
    def add_action_to_flow_entry(tx: Transaction, flow_entry_id, action_id):
        CREATE_HAS_MATCH_RELATION = """
        MERGE (entry:FlowEntry {flow_entry_id: $flow_entry_id})
        MERGE (action:Action {action_id: $action_id})
        MERGE (entry)-[:hasAction]->(action)
        """
        tx.run(
            CREATE_HAS_MATCH_RELATION, flow_entry_id=flow_entry_id, action_id=action_id
        )

    @staticmethod
    def delete_flow_entry_from_switch(tx: Transaction, dpid, flow_entry_id):
        DELETE_HAS_FLOW_ENTRY_RELATION = """
        MATCH (OpenFlowSwitch {dpid: $dpid})-[rel:hasFlowEntry]->(FlowEntry {flow_entry_id: $flow_entry_id})
        DELETE rel
        """
        tx.run(DELETE_HAS_FLOW_ENTRY_RELATION, dpid=dpid, flow_entry_id=flow_entry_id)

    @staticmethod
    def delete_switch(tx: Transaction, dpid):
        DELETE_SWITCH = """
        MATCH (switch:OpenFlowSwitch {dpid:$dpid}) DETACH DELETE switch
        """
        tx.run(DELETE_SWITCH, dpid=dpid)
