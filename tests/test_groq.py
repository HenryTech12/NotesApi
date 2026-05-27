import pytest
from unittest.mock import AsyncMock, patch
import uuid
from src.services.groq_service import summarize, suggest_tags

from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_summarize_mock():
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": "This is a mocked summary."
                }
            }
        ]
    }
    
    with patch("src.services.groq_service.GROQ_API_KEY", "mock-key"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            # Create a mock response object
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            
            mock_post.return_value = mock_resp
            
            summary, meta = await summarize("Some long text to summarize.")
            
            assert summary == "This is a mocked summary."
            assert meta["cached"] is False

@pytest.mark.asyncio
async def test_suggest_tags_mock():
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": "tag1, tag2, tag3"
                }
            }
        ]
    }
    
    with patch("src.services.groq_service.GROQ_API_KEY", "mock-key"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            # Create a mock response object
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            
            mock_post.return_value = mock_resp
            
            tags, meta = await suggest_tags("Some text to tag.")
            
            assert tags == ["tag1", "tag2", "tag3"]
            assert meta["cached"] is False
