from app.domain.models.connector import ConnectorCatalogItem, ConnectorEnvField
from app.domain.models.mcp_config import MCPTransport

OFFICIAL_CONNECTORS: list[ConnectorCatalogItem] = [
    ConnectorCatalogItem(
        id="github",
        name="GitHub",
        description="Search repositories, issues, and pull requests",
        category="development",
        icon_url="https://github.githubassets.com/favicons/favicon.svg",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env_fields=[
            ConnectorEnvField(
                key="GITHUB_TOKEN",
                label="GitHub Token",
                secret=True,
                placeholder="ghp_...",
            ),
        ],
    ),
    ConnectorCatalogItem(
        id="filesystem",
        name="Filesystem",
        description="Read and write files in a sandbox directory",
        category="development",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    ),
    ConnectorCatalogItem(
        id="notion",
        name="Notion",
        description="Search and update Notion pages and databases",
        category="productivity",
        icon_url="https://www.notion.so/images/favicon.ico",
        transport=MCPTransport.STREAMABLE_HTTP,
        url="https://mcp.notion.com/mcp",
        header_fields=[
            ConnectorEnvField(
                key="Authorization",
                label="Notion Integration Token",
                secret=True,
                placeholder="Bearer secret_...",
            ),
        ],
    ),
    ConnectorCatalogItem(
        id="slack",
        name="Slack",
        description="Send messages and read channels in Slack",
        category="productivity",
        transport=MCPTransport.STREAMABLE_HTTP,
        url="https://mcp.slack.com/mcp",
        header_fields=[
            ConnectorEnvField(
                key="Authorization",
                label="Slack Bot Token",
                secret=True,
                placeholder="Bearer xoxb-...",
            ),
        ],
    ),
    ConnectorCatalogItem(
        id="gmail",
        name="Gmail",
        description="Search and draft emails in Gmail",
        category="productivity",
        transport=MCPTransport.STREAMABLE_HTTP,
        url="https://mcp.googleapis.com/gmail/mcp",
        header_fields=[
            ConnectorEnvField(
                key="Authorization",
                label="Google OAuth Token",
                secret=True,
                placeholder="Bearer ya29...",
            ),
        ],
    ),
    ConnectorCatalogItem(
        id="google-calendar",
        name="Google Calendar",
        description="Read and create calendar events",
        category="productivity",
        transport=MCPTransport.STREAMABLE_HTTP,
        url="https://mcp.googleapis.com/calendar/mcp",
        header_fields=[
            ConnectorEnvField(
                key="Authorization",
                label="Google OAuth Token",
                secret=True,
                placeholder="Bearer ya29...",
            ),
        ],
    ),
    ConnectorCatalogItem(
        id="google-drive",
        name="Google Drive",
        description="Search and read files in Google Drive",
        category="productivity",
        transport=MCPTransport.STREAMABLE_HTTP,
        url="https://mcp.googleapis.com/drive/mcp",
        header_fields=[
            ConnectorEnvField(
                key="Authorization",
                label="Google OAuth Token",
                secret=True,
                placeholder="Bearer ya29...",
            ),
        ],
    ),
    ConnectorCatalogItem(
        id="hubspot",
        name="HubSpot",
        description="Manage contacts, deals, and CRM records",
        category="business",
        transport=MCPTransport.STREAMABLE_HTTP,
        url="https://mcp.hubspot.com/mcp",
        header_fields=[
            ConnectorEnvField(
                key="Authorization",
                label="HubSpot Private App Token",
                secret=True,
                placeholder="Bearer pat-...",
            ),
        ],
    ),
    ConnectorCatalogItem(
        id="stripe",
        name="Stripe",
        description="Query payments, customers, and subscriptions",
        category="business",
        transport=MCPTransport.STREAMABLE_HTTP,
        url="https://mcp.stripe.com/mcp",
        header_fields=[
            ConnectorEnvField(
                key="Authorization",
                label="Stripe Secret Key",
                secret=True,
                placeholder="Bearer sk_live_...",
            ),
        ],
    ),
    ConnectorCatalogItem(
        id="huggingface",
        name="Hugging Face",
        description="Search models, datasets, and spaces",
        category="development",
        icon_url="https://huggingface.co/favicon.ico",
        transport=MCPTransport.STREAMABLE_HTTP,
        url="https://mcp.huggingface.co/mcp",
        header_fields=[
            ConnectorEnvField(
                key="Authorization",
                label="Hugging Face Token",
                secret=True,
                placeholder="Bearer hf_...",
            ),
        ],
    ),
]

OFFICIAL_CONNECTOR_BY_ID = {item.id: item for item in OFFICIAL_CONNECTORS}
