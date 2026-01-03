"""
Example: Testing LLM Module
Epic 1: 本地模型集成与管理

This script demonstrates how to use the LLM module.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.llm import (
    get_llm_manager,
    get_health_checker,
    Message,
)


async def test_health_check():
    """Test health check"""
    print("=" * 60)
    print("1. Health Check")
    print("=" * 60)

    checker = get_health_checker()
    results = await checker.check_all()

    for service, status in results.items():
        print(f"\n{service}:")
        print(f"  Status: {status.status}")
        if status.details:
            for key, value in status.details.items():
                print(f"  {key}: {value}")
        if status.error:
            print(f"  Error: {status.error}")

    overall = checker.get_overall_status(results)
    print(f"\nOverall Status: {overall}")


async def test_generate():
    """Test text generation"""
    print("\n" + "=" * 60)
    print("2. Text Generation (Non-streaming)")
    print("=" * 60)

    manager = get_llm_manager()
    llm = manager.create_llm()

    print(f"\nUsing model: {llm.model_name}")
    print(f"Host: {llm.host}")

    prompt = "用一句话介绍什么是人工智能"
    print(f"\nPrompt: {prompt}")
    print("\nGenerating...")

    try:
        response = await llm.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=100
        )

        print(f"\nResponse: {response.content}")
        print(f"\nStats:")
        print(f"  Tokens: {response.eval_count}")
        if response.eval_duration:
            seconds = response.eval_duration / 1e9
            tokens_per_sec = response.eval_count / seconds if seconds > 0 else 0
            print(f"  Speed: {tokens_per_sec:.2f} tokens/sec")
    except Exception as e:
        print(f"\nError: {e}")


async def test_chat():
    """Test chat conversation"""
    print("\n" + "=" * 60)
    print("3. Chat Conversation")
    print("=" * 60)

    manager = get_llm_manager()
    llm = manager.create_llm()

    messages = [
        Message(role="system", content="你是一个友好的AI助手"),
        Message(role="user", content="你好"),
        Message(role="assistant", content="你好！我是AI助手，很高兴见到你。"),
        Message(role="user", content="请推荐一本Python书籍"),
    ]

    print("\nConversation:")
    for msg in messages:
        print(f"  [{msg.role}]: {msg.content}")

    print("\n[Generating response...]")

    try:
        response = await llm.chat(messages=messages, temperature=0.7)
        print(f"  [assistant]: {response.content}")
    except Exception as e:
        print(f"\nError: {e}")


async def test_stream():
    """Test streaming generation"""
    print("\n" + "=" * 60)
    print("4. Streaming Generation")
    print("=" * 60)

    manager = get_llm_manager()
    llm = manager.create_llm()

    prompt = "讲一个简短的笑话"
    print(f"\nPrompt: {prompt}")
    print("\nResponse (streaming): ", end="", flush=True)

    try:
        async for chunk in llm.generate_stream(prompt=prompt, max_tokens=100):
            print(chunk, end="", flush=True)
        print()  # New line at the end
    except Exception as e:
        print(f"\nError: {e}")


async def test_embedding():
    """Test text embedding"""
    print("\n" + "=" * 60)
    print("5. Text Embedding")
    print("=" * 60)

    manager = get_llm_manager()

    # Note: You need to download the embedding model first:
    # docker exec ktbot-ollama ollama pull bge-large-zh

    try:
        embedding = manager.create_embedding()
        print(f"\nUsing model: {embedding.model_name}")

        text = "人工智能是计算机科学的一个分支"
        print(f"\nText: {text}")
        print("\nGenerating embedding...")

        response = await embedding.embed(text=text)

        print(f"\nEmbedding dimension: {len(response.embedding)}")
        print(f"First 10 values: {response.embedding[:10]}")
    except Exception as e:
        print(f"\nError: {e}")
        print("Note: Make sure to download the embedding model first:")
        print("  docker exec ktbot-ollama ollama pull bge-large-zh")


async def main():
    """Main function"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "KT-BOT LLM Module Test" + " " * 21 + "║")
    print("╚" + "═" * 58 + "╝")

    try:
        # Test 1: Health check
        await test_health_check()

        # Test 2: Generate (non-streaming)
        await test_generate()

        # Test 3: Chat
        await test_chat()

        # Test 4: Stream
        await test_stream()

        # Test 5: Embedding (optional)
        # Uncomment if you have the embedding model downloaded
        # await test_embedding()

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        manager = get_llm_manager()
        await manager.close_all()
        print("\n\nAll connections closed.")


if __name__ == "__main__":
    asyncio.run(main())
