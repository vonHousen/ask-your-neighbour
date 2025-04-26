from diagrams import Cluster, Diagram, Edge
from diagrams.generic.compute import Rack
from diagrams.onprem.client import User
from diagrams.programming.language import Python


# TODO:test if this works
def create_diagram():
    with Diagram("Ask Your Neighbour Agents Architecture", show=False, filename="img/agents_architecture.png"):
        user = User("User")

        with Cluster("Agent System"):
            orchestrator = Python("Orchestrator Agent")

            with Cluster("Specialized Agents"):
                location = Python("Location Explorer")
                document = Python("Document Explorer")
                search = Python("Search Agent")
                summarization = Python("Summarization Agent")

            with Cluster("Visualization Tools"):
                vis_map = Python("Visualize Map Tool")
                vis_plan = Python("Visualize Plan Tool")

            with Cluster("External Services"):
                mcp_server = Rack("MCP Server")

        # Connect components
        user >> Edge(label="query") >> orchestrator
        orchestrator >> Edge() >> location
        orchestrator >> Edge() >> document
        orchestrator >> Edge() >> search
        orchestrator >> Edge(label="handoff") >> summarization

        # Tools connections
        orchestrator >> Edge() >> vis_map
        orchestrator >> Edge() >> vis_plan

        # Service connections
        location >> Edge() >> mcp_server

        # Response flow
        orchestrator >> Edge(label="response") >> user
