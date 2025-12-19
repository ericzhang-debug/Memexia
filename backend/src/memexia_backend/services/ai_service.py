"""
AI service for node expansion and intelligent features.

Implements OpenAI-compatible API integration with streaming support.
"""

import json
import random
from typing import Any, AsyncGenerator, Optional
from openai import AsyncOpenAI
from loguru import logger

from memexia_backend.config import settings
from memexia_backend.schemas import NodeCreate, EdgeCreate
from . import graph_service


class AIService:
    """AI service for generating related nodes and intelligent expansion."""

    def __init__(self):
        """Initialize the OpenAI client."""
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not configured")
            self._client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
            )
        return self._client

    def _build_expansion_prompt(
        self,
        source_content: str,
        instruction: Optional[str] = None,
    ) -> str:
        """Build the system prompt for node expansion."""
        base_prompt = f"""You are an intelligent knowledge expansion assistant. Your task is to generate related concepts based on the given node content.

Given node content: "{source_content}"

Generate exactly 3 related concepts that:
1. Are logically connected to the source concept
2. Provide new perspectives or deeper understanding
3. Are concise but informative (1-2 sentences each)

{f'Additional instruction: {instruction}' if instruction else ''}

Respond in JSON format with the following structure:
{{
    "concepts": [
        {{
            "content": "The concept description",
            "relation": "How this relates to the source (e.g., 'is a type of', 'is caused by', 'leads to')"
        }}
    ]
}}

Only respond with valid JSON, no additional text."""
        return base_prompt

    async def expand_node_stream(
        self,
        collection: Any,
        node_id: str,
        knowledge_base_id: str,
        instruction: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream AI expansion of a node using OpenAI API.

        Yields SSE-formatted events for real-time updates.

        Args:
            collection: ChromaDB collection
            node_id: Node ID to expand
            knowledge_base_id: Knowledge base ID
            instruction: Optional instruction for expansion

        Yields:
            SSE event strings
        """
        source_node = graph_service.get_node(node_id, knowledge_base_id)
        if not source_node:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Node not found'})}\n\n"
            return

        # Send start event
        yield f"data: {json.dumps({'type': 'start', 'source_node': {'id': source_node.id, 'content': source_node.content}})}\n\n"

        try:
            # Check if API key is configured
            if not settings.OPENAI_API_KEY:
                logger.warning("OpenAI API key not configured, using mock expansion")
                async for event in self._mock_expand_stream(
                    collection, source_node, knowledge_base_id, instruction
                ):
                    yield event
                return

            # Build prompt and call OpenAI
            prompt = self._build_expansion_prompt(source_node.content, instruction)

            # Stream the response
            full_response = ""
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'AI is analyzing the concept...'})}\n\n"

            stream = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful knowledge expansion assistant."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n"

            # Parse the response and create nodes
            yield f"data: {json.dumps({'type': 'parsing', 'message': 'Creating new nodes...'})}\n\n"

            try:
                # Try to extract JSON from the response
                json_start = full_response.find("{")
                json_end = full_response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = full_response[json_start:json_end]
                    parsed = json.loads(json_str)
                    concepts = parsed.get("concepts", [])
                else:
                    raise ValueError("No valid JSON found in response")

                created_nodes = []
                for concept in concepts:
                    content = concept.get("content", "")
                    relation = concept.get("relation", "related_to")

                    if not content:
                        continue

                    # Create new node
                    new_node_data = NodeCreate(content=content, node_type="generated")
                    new_node = graph_service.create_node(
                        collection, new_node_data, knowledge_base_id
                    )
                    created_nodes.append(new_node)

                    # Create edge
                    edge_data = EdgeCreate(
                        source_id=source_node.id,
                        target_id=new_node.id,
                        relation_type=relation if isinstance(relation, str) else "ai_generated",
                        weight=random.randint(3, 5),
                    )
                    graph_service.create_edge(edge_data, knowledge_base_id)

                    # Send node created event
                    yield f"data: {json.dumps({'type': 'node_created', 'node': {'id': new_node.id, 'content': new_node.content, 'node_type': new_node.node_type}, 'relation': relation})}\n\n"

                # Send completion event
                yield f"data: {json.dumps({'type': 'complete', 'total_nodes': len(created_nodes)})}\n\n"

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response: {e}")
                # Fallback: create a single node with the response
                new_node_data = NodeCreate(
                    content=full_response[:500] if len(full_response) > 500 else full_response,
                    node_type="generated",
                )
                new_node = graph_service.create_node(
                    collection, new_node_data, knowledge_base_id
                )

                edge_data = EdgeCreate(
                    source_id=source_node.id,
                    target_id=new_node.id,
                    relation_type="ai_generated",
                    weight=3,
                )
                graph_service.create_edge(edge_data, knowledge_base_id)

                yield f"data: {json.dumps({'type': 'node_created', 'node': {'id': new_node.id, 'content': new_node.content, 'node_type': new_node.node_type}, 'relation': 'ai_generated'})}\n\n"
                yield f"data: {json.dumps({'type': 'complete', 'total_nodes': 1})}\n\n"

        except Exception as e:
            logger.error(f"AI expansion error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    async def _mock_expand_stream(
        self,
        collection: Any,
        source_node: Any,
        knowledge_base_id: str,
        instruction: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Mock expansion for testing without OpenAI API.

        Used when OPENAI_API_KEY is not configured.
        """
        import asyncio

        yield f"data: {json.dumps({'type': 'thinking', 'message': 'AI is analyzing the concept... (mock mode)'})}\n\n"
        await asyncio.sleep(0.5)

        # Generate mock concepts
        mock_concepts = [
            {"content": f"An aspect of {source_node.content}: deeper understanding of its core principles", "relation": "aspect_of"},
            {"content": f"Application of {source_node.content}: practical use cases and implementations", "relation": "application_of"},
            {"content": f"Related to {source_node.content}: connections to adjacent concepts", "relation": "related_to"},
        ]

        # Simulate streaming chunks
        for concept in mock_concepts:
            yield f"data: {json.dumps({'type': 'chunk', 'content': concept['content']})}\n\n"
            await asyncio.sleep(0.3)

        yield f"data: {json.dumps({'type': 'parsing', 'message': 'Creating new nodes...'})}\n\n"
        await asyncio.sleep(0.3)

        created_nodes = []
        for concept in mock_concepts:
            new_node_data = NodeCreate(content=concept["content"], node_type="generated")
            new_node = graph_service.create_node(
                collection, new_node_data, knowledge_base_id
            )
            created_nodes.append(new_node)

            edge_data = EdgeCreate(
                source_id=source_node.id,
                target_id=new_node.id,
                relation_type=concept["relation"],
                weight=random.randint(3, 5),
            )
            graph_service.create_edge(edge_data, knowledge_base_id)

            yield f"data: {json.dumps({'type': 'node_created', 'node': {'id': new_node.id, 'content': new_node.content, 'node_type': new_node.node_type}, 'relation': concept['relation']})}\n\n"
            await asyncio.sleep(0.2)

        yield f"data: {json.dumps({'type': 'complete', 'total_nodes': len(created_nodes)})}\n\n"

    def expand_node(
        self,
        collection: Any,
        node_id: str,
        knowledge_base_id: str,
        instruction: str | None = None,
    ):
        """
        Synchronous expansion of a node (legacy method).

        For streaming expansion, use expand_node_stream instead.

        Args:
            collection: ChromaDB collection
            node_id: Node ID to expand
            knowledge_base_id: Knowledge base ID
            instruction: Optional instruction for expansion

        Returns:
            List of created nodes
        """
        source_node = graph_service.get_node(node_id, knowledge_base_id)
        if not source_node:
            raise ValueError("Node not found")

        # Mock logic: Generate 2-3 related concepts
        new_concepts = [
            f"Related to {source_node.content} - A",
            f"Related to {source_node.content} - B",
            f"Implication of {source_node.content}",
        ]

        created_nodes = []
        for concept in new_concepts:
            # Create new node
            new_node_data = NodeCreate(content=concept, node_type="generated")
            new_node = graph_service.create_node(
                collection, new_node_data, knowledge_base_id
            )
            created_nodes.append(new_node)

            # Create edge
            edge_data = EdgeCreate(
                source_id=source_node.id,
                target_id=new_node.id,
                relation_type="suggested_by_ai",
                weight=random.randint(1, 5),
            )
            graph_service.create_edge(edge_data, knowledge_base_id)

        return created_nodes


ai_service = AIService()
