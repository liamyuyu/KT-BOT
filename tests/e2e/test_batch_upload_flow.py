"""
End-to-End Tests for Batch Upload Flow

Tests the complete batch upload workflow from file submission
to document indexing and retrieval.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import List
import pytest
import aiohttp
from fastapi.testclient import TestClient

from src.main import app
from src.services.upload import get_upload_manager
from src.services.upload.models import UploadStatus
from src.services.document.service import get_document_service


class TestBatchUploadFlow:
    """End-to-end tests for complete batch upload workflow"""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment"""
        self.client = TestClient(app)
        self.manager = get_upload_manager()
        self.doc_service = get_document_service()
        self.base_url = "http://localhost:7860/api/v1"
        self.test_files_dir = tempfile.mkdtemp()

        # Create test files
        self.test_files = self._create_test_files()

        yield

        # Cleanup
        for file_path in self.test_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        os.rmdir(self.test_files_dir)

    def _create_test_files(self) -> List[str]:
        """Create test files of different types"""
        files = []

        # 1. PDF file (simulated)
        pdf_path = os.path.join(self.test_files_dir, "test.pdf")
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n%Test PDF content\n")
        files.append(pdf_path)

        # 2. HTML file
        html_path = os.path.join(self.test_files_dir, "test.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("""
<!DOCTYPE html>
<html>
<head><title>Test Document</title></head>
<body>
    <h1>Test Heading</h1>
    <p>This is test content for E2E testing.</p>
</body>
</html>
            """)
        files.append(html_path)

        # 3. Markdown file
        md_path = os.path.join(self.test_files_dir, "test.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("""
# Test Markdown Document

This is a test markdown file for E2E testing.

## Section 1

Test content here.
            """)
        files.append(md_path)

        # 4. DOCX file (simulated ZIP)
        docx_path = os.path.join(self.test_files_dir, "test.docx")
        with open(docx_path, "wb") as f:
            f.write(b"PK\x03\x04Test DOCX content\n")
        files.append(docx_path)

        # 5. Another HTML file
        html2_path = os.path.join(self.test_files_dir, "test2.html")
        with open(html2_path, "w", encoding="utf-8") as f:
            f.write("""
<!DOCTYPE html>
<html>
<head><title>Second Test</title></head>
<body>
    <article>
        <h1>Article Title</h1>
        <p>Article content for testing.</p>
    </article>
</body>
</html>
            """)
        files.append(html2_path)

        return files

    @pytest.mark.asyncio
    async def test_complete_batch_upload_flow(self):
        """
        Test complete batch upload flow:
        1. Submit batch upload
        2. Monitor progress
        3. Verify all tasks complete
        4. Verify documents are indexed
        5. Query upload history
        """
        # Step 1: Submit batch upload
        files_data = []
        for file_path in self.test_files:
            files_data.append(
                ("files", (os.path.basename(file_path), open(file_path, "rb")))
            )

        response = self.client.post(
            "/api/v1/documents/batch-upload",
            params={"user_id": "test_user"},
            data={"tags": "test,e2e"},
            files=files_data
        )

        assert response.status_code == 200
        result = response.json()

        assert "batch_id" in result
        assert result["total_files"] == 5
        assert result["accepted_files"] == 5
        assert len(result["task_ids"]) == 5

        batch_id = result["batch_id"]
        task_ids = result["task_ids"]

        # Step 2: Monitor progress for all tasks
        completed_tasks = []
        max_wait = 60  # 60 seconds timeout
        start_time = asyncio.get_event_loop().time()

        while len(completed_tasks) < len(task_ids):
            if asyncio.get_event_loop().time() - start_time > max_wait:
                pytest.fail("Timeout waiting for tasks to complete")

            # Check each task status
            for task_id in task_ids:
                if task_id in completed_tasks:
                    continue

                task = await self.manager.get_task_status(task_id)
                assert task is not None

                if task.status in [
                    UploadStatus.COMPLETED,
                    UploadStatus.FAILED,
                    UploadStatus.CANCELLED
                ]:
                    completed_tasks.append(task_id)

                    # Verify completed tasks
                    if task.status == UploadStatus.COMPLETED:
                        assert task.progress_percentage == 100.0
                        assert task.document_id is not None
                        assert task.completed_at is not None

            await asyncio.sleep(0.5)

        # Step 3: Verify all tasks completed successfully
        all_completed = True
        document_ids = []

        for task_id in task_ids:
            task = await self.manager.get_task_status(task_id)
            if task.status == UploadStatus.COMPLETED:
                document_ids.append(task.document_id)
            else:
                all_completed = False

        assert all_completed, "Not all tasks completed successfully"
        assert len(document_ids) == 5

        # Step 4: Verify documents are indexed in ChromaDB
        for doc_id in document_ids:
            doc = await self.doc_service.get_document(doc_id)
            assert doc is not None
            assert doc.id == doc_id
            assert "test" in doc.tags or "e2e" in doc.tags

        # Step 5: Query upload history
        response = self.client.get(
            "/api/v1/documents/upload/tasks",
            params={"user_id": "test_user", "limit": 50}
        )

        assert response.status_code == 200
        tasks = response.json()

        # Verify our batch is in the history
        batch_tasks = [t for t in tasks if t["batch_id"] == batch_id]
        assert len(batch_tasks) == 5

        for task in batch_tasks:
            assert task["status"] == "completed"
            assert task["progress_percentage"] == 100.0
            assert task["document_id"] is not None

    @pytest.mark.asyncio
    async def test_concurrent_batch_uploads(self):
        """
        Test concurrent batch uploads:
        1. Submit 2 batches simultaneously (10 files total)
        2. Verify concurrency control (max 3 concurrent)
        3. Verify all tasks complete
        """
        # Prepare 2 batches of files
        batch1_files = self.test_files[:3]  # 3 files
        batch2_files = self.test_files[3:]  # 2 files

        # Submit both batches concurrently
        async def submit_batch(files: List[str], user_id: str):
            files_data = []
            for file_path in files:
                files_data.append(
                    ("files", (os.path.basename(file_path), open(file_path, "rb")))
                )

            response = self.client.post(
                "/api/v1/documents/batch-upload",
                params={"user_id": user_id},
                files=files_data
            )
            return response.json()

        results = await asyncio.gather(
            submit_batch(batch1_files, "user1"),
            submit_batch(batch2_files, "user2")
        )

        batch1_result = results[0]
        batch2_result = results[1]

        assert batch1_result["accepted_files"] == 3
        assert batch2_result["accepted_files"] == 2

        all_task_ids = batch1_result["task_ids"] + batch2_result["task_ids"]

        # Monitor concurrency - at most 3 should be processing at once
        max_concurrent = 0
        completed = set()

        while len(completed) < len(all_task_ids):
            current_processing = 0

            for task_id in all_task_ids:
                if task_id in completed:
                    continue

                task = await self.manager.get_task_status(task_id)

                if task.status in [
                    UploadStatus.COMPLETED,
                    UploadStatus.FAILED,
                    UploadStatus.CANCELLED
                ]:
                    completed.add(task_id)
                elif task.status in [
                    UploadStatus.VALIDATING,
                    UploadStatus.PARSING,
                    UploadStatus.INDEXING
                ]:
                    current_processing += 1

            max_concurrent = max(max_concurrent, current_processing)
            await asyncio.sleep(0.2)

        # Verify concurrency was respected
        assert max_concurrent <= 3, f"Concurrency exceeded limit: {max_concurrent}"

        # Verify all completed
        assert len(completed) == 5

    @pytest.mark.asyncio
    async def test_upload_with_failures(self):
        """
        Test upload with some invalid files:
        1. Upload batch with valid and invalid files
        2. Verify partial success
        3. Verify error messages are correct
        """
        # Create an invalid file
        invalid_path = os.path.join(self.test_files_dir, "invalid.xyz")
        with open(invalid_path, "w") as f:
            f.write("Invalid file type")

        # Create an oversized file (simulate)
        large_path = os.path.join(self.test_files_dir, "large.pdf")
        with open(large_path, "wb") as f:
            # Write 51MB of data (exceeds 50MB limit)
            f.write(b"%PDF-1.4\n")
            f.write(b"X" * (51 * 1024 * 1024))

        # Submit batch with valid and invalid files
        files_data = [
            ("files", (os.path.basename(self.test_files[0]), open(self.test_files[0], "rb"))),
            ("files", ("invalid.xyz", open(invalid_path, "rb"))),
            ("files", ("large.pdf", open(large_path, "rb"))),
        ]

        response = self.client.post(
            "/api/v1/documents/batch-upload",
            params={"user_id": "test_user"},
            files=files_data
        )

        assert response.status_code == 200
        result = response.json()

        # Verify partial acceptance
        assert result["total_files"] == 3
        assert result["accepted_files"] == 1
        assert len(result["rejected_files"]) == 2

        # Verify error messages
        rejected = {r["file_name"]: r["reason"] for r in result["rejected_files"]}
        assert "invalid.xyz" in rejected
        assert "不支持的文件类型" in rejected["invalid.xyz"]

        assert "large.pdf" in rejected
        assert "文件大小超过限制" in rejected["large.pdf"]

        # Verify the valid file was processed
        assert len(result["task_ids"]) == 1

        # Wait for task to complete
        task_id = result["task_ids"][0]
        max_wait = 30
        start_time = asyncio.get_event_loop().time()

        while True:
            if asyncio.get_event_loop().time() - start_time > max_wait:
                pytest.fail("Timeout waiting for task to complete")

            task = await self.manager.get_task_status(task_id)
            if task.status in [UploadStatus.COMPLETED, UploadStatus.FAILED]:
                break

            await asyncio.sleep(0.5)

        # Verify successful completion
        task = await self.manager.get_task_status(task_id)
        assert task.status == UploadStatus.COMPLETED
        assert task.document_id is not None

        # Cleanup
        os.remove(invalid_path)
        os.remove(large_path)

    @pytest.mark.asyncio
    async def test_task_cancellation(self):
        """
        Test task cancellation:
        1. Submit batch upload
        2. Cancel a task mid-processing
        3. Verify task is cancelled
        4. Verify other tasks continue
        """
        # Submit batch
        files_data = []
        for file_path in self.test_files[:3]:  # Use 3 files
            files_data.append(
                ("files", (os.path.basename(file_path), open(file_path, "rb")))
            )

        response = self.client.post(
            "/api/v1/documents/batch-upload",
            params={"user_id": "test_user"},
            files=files_data
        )

        result = response.json()
        task_ids = result["task_ids"]

        # Wait a moment for processing to start
        await asyncio.sleep(1)

        # Cancel first task
        cancel_response = self.client.post(
            f"/api/v1/documents/upload/{task_ids[0]}/cancel"
        )

        assert cancel_response.status_code == 200
        cancel_result = cancel_response.json()
        assert cancel_result["success"] is True

        # Wait for all tasks to finish
        await asyncio.sleep(10)

        # Verify first task is cancelled
        task0 = await self.manager.get_task_status(task_ids[0])
        assert task0.status == UploadStatus.CANCELLED

        # Verify other tasks completed
        task1 = await self.manager.get_task_status(task_ids[1])
        task2 = await self.manager.get_task_status(task_ids[2])

        # At least one should have completed
        completed_count = sum([
            1 for t in [task1, task2]
            if t.status == UploadStatus.COMPLETED
        ])
        assert completed_count >= 1

    @pytest.mark.asyncio
    async def test_sse_progress_stream(self):
        """
        Test SSE progress stream:
        1. Submit upload
        2. Connect to SSE endpoint
        3. Verify progress events are received
        4. Verify event sequence is correct
        """
        # Submit single file upload
        file_path = self.test_files[0]
        files_data = [
            ("files", (os.path.basename(file_path), open(file_path, "rb")))
        ]

        response = self.client.post(
            "/api/v1/documents/batch-upload",
            params={"user_id": "test_user"},
            files=files_data
        )

        result = response.json()
        task_id = result["task_ids"][0]

        # Connect to SSE endpoint
        progress_events = []

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/documents/upload/{task_id}/progress"
            ) as resp:
                async for line in resp.content:
                    if line.startswith(b"data: "):
                        import json
                        data = json.loads(line[6:])
                        progress_events.append(data)

                        # Break when completed
                        if data["status"] in ["completed", "failed", "cancelled"]:
                            break

        # Verify events were received
        assert len(progress_events) > 0

        # Verify event sequence
        statuses = [e["status"] for e in progress_events]

        # Should include validating, parsing, indexing, completed
        assert "validating" in statuses or "pending" in statuses
        assert "completed" in statuses or "failed" in statuses

        # Progress should increase
        progresses = [e["progress_percentage"] for e in progress_events]
        assert progresses[-1] >= progresses[0]

        # Final event should be completed
        assert progress_events[-1]["status"] == "completed"
        assert progress_events[-1]["progress_percentage"] == 100.0


class TestUploadPerformance:
    """Performance tests for upload system"""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment"""
        self.client = TestClient(app)
        self.manager = get_upload_manager()
        self.test_files_dir = tempfile.mkdtemp()

        yield

        # Cleanup
        import shutil
        shutil.rmtree(self.test_files_dir, ignore_errors=True)

    def _create_large_file(self, size_mb: int, file_type: str = "pdf") -> str:
        """Create a large test file"""
        if file_type == "pdf":
            filename = f"large_{size_mb}mb.pdf"
            file_path = os.path.join(self.test_files_dir, filename)

            with open(file_path, "wb") as f:
                f.write(b"%PDF-1.4\n")
                f.write(b"X" * (size_mb * 1024 * 1024 - 10))

        elif file_type == "html":
            filename = f"large_{size_mb}mb.html"
            file_path = os.path.join(self.test_files_dir, filename)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write("<!DOCTYPE html><html><head><title>Large</title></head><body>")
                # Write lots of content
                content_size = size_mb * 1024 * 1024 - 100
                f.write("A" * content_size)
                f.write("</body></html>")

        return file_path

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_large_file_upload_10mb(self):
        """Test 10MB file upload performance"""
        import time

        # Create 10MB file
        file_path = self._create_large_file(10, "pdf")

        # Submit upload
        start_time = time.time()

        files_data = [("files", (os.path.basename(file_path), open(file_path, "rb")))]
        response = self.client.post(
            "/api/v1/documents/batch-upload",
            params={"user_id": "test_user"},
            files=files_data
        )

        assert response.status_code == 200
        result = response.json()
        task_id = result["task_ids"][0]

        # Wait for completion
        while True:
            task = await self.manager.get_task_status(task_id)
            if task.status in [UploadStatus.COMPLETED, UploadStatus.FAILED]:
                break
            await asyncio.sleep(0.5)

        elapsed = time.time() - start_time

        # Verify performance target: < 20 seconds
        assert elapsed < 20, f"10MB upload took {elapsed:.2f}s (target: <20s)"

        # Verify success
        task = await self.manager.get_task_status(task_id)
        assert task.status == UploadStatus.COMPLETED

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_large_file_upload_40mb(self):
        """Test 40MB file upload performance"""
        import time

        # Create 40MB file
        file_path = self._create_large_file(40, "pdf")

        # Submit upload
        start_time = time.time()

        files_data = [("files", (os.path.basename(file_path), open(file_path, "rb")))]
        response = self.client.post(
            "/api/v1/documents/batch-upload",
            params={"user_id": "test_user"},
            files=files_data
        )

        assert response.status_code == 200
        result = response.json()
        task_id = result["task_ids"][0]

        # Wait for completion
        while True:
            task = await self.manager.get_task_status(task_id)
            if task.status in [UploadStatus.COMPLETED, UploadStatus.FAILED]:
                break
            await asyncio.sleep(0.5)

        elapsed = time.time() - start_time

        # Verify performance target: < 60 seconds
        assert elapsed < 60, f"40MB upload took {elapsed:.2f}s (target: <60s)"

        # Verify success
        task = await self.manager.get_task_status(task_id)
        assert task.status == UploadStatus.COMPLETED

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_10_files_upload(self):
        """Test 10 files concurrent upload performance"""
        import time

        # Create 10 small files (1MB each)
        file_paths = []
        for i in range(10):
            file_path = self._create_large_file(1, "pdf")
            # Rename to unique name
            new_path = os.path.join(
                self.test_files_dir,
                f"concurrent_{i}.pdf"
            )
            os.rename(file_path, new_path)
            file_paths.append(new_path)

        # Submit batch upload
        start_time = time.time()

        files_data = []
        for file_path in file_paths:
            files_data.append(
                ("files", (os.path.basename(file_path), open(file_path, "rb")))
            )

        response = self.client.post(
            "/api/v1/documents/batch-upload",
            params={"user_id": "test_user"},
            files=files_data
        )

        assert response.status_code == 200
        result = response.json()
        task_ids = result["task_ids"]

        # Wait for all to complete
        completed = set()
        while len(completed) < len(task_ids):
            for task_id in task_ids:
                if task_id in completed:
                    continue

                task = await self.manager.get_task_status(task_id)
                if task.status in [UploadStatus.COMPLETED, UploadStatus.FAILED]:
                    completed.add(task_id)

            await asyncio.sleep(0.5)

        elapsed = time.time() - start_time

        # Verify performance target: < 5 minutes (300s)
        assert elapsed < 300, f"10 files upload took {elapsed:.2f}s (target: <300s)"

        # Verify all completed
        assert len(completed) == 10

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test memory usage during upload"""
        import psutil
        import os as os_module

        process = psutil.Process(os_module.getpid())

        # Get baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create and upload 5 files (10MB each)
        file_paths = []
        for i in range(5):
            file_path = self._create_large_file(10, "pdf")
            new_path = os.path.join(
                self.test_files_dir,
                f"memory_test_{i}.pdf"
            )
            os.rename(file_path, new_path)
            file_paths.append(new_path)

        # Submit upload
        files_data = []
        for file_path in file_paths:
            files_data.append(
                ("files", (os.path.basename(file_path), open(file_path, "rb")))
            )

        response = self.client.post(
            "/api/v1/documents/batch-upload",
            params={"user_id": "test_user"},
            files=files_data
        )

        result = response.json()
        task_ids = result["task_ids"]

        # Monitor memory during processing
        max_memory = baseline_memory
        completed = set()

        while len(completed) < len(task_ids):
            current_memory = process.memory_info().rss / 1024 / 1024
            max_memory = max(max_memory, current_memory)

            for task_id in task_ids:
                if task_id in completed:
                    continue

                task = await self.manager.get_task_status(task_id)
                if task.status in [UploadStatus.COMPLETED, UploadStatus.FAILED]:
                    completed.add(task_id)

            await asyncio.sleep(0.5)

        memory_increase = max_memory - baseline_memory

        # Verify memory increase < 200MB
        assert memory_increase < 200, f"Memory increased by {memory_increase:.2f}MB (target: <200MB)"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_api_response_time(self):
        """Test API endpoint response times"""
        import time

        # Test batch upload endpoint response time (not including processing)
        files_data = [
            ("files", ("test.pdf", b"%PDF-1.4\ntest content"))
        ]

        start_time = time.time()
        response = self.client.post(
            "/api/v1/documents/batch-upload",
            params={"user_id": "test_user"},
            files=files_data
        )
        elapsed_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        # API should respond quickly (< 100ms for submission)
        assert elapsed_ms < 100, f"API response took {elapsed_ms:.2f}ms (target: <100ms)"

        result = response.json()
        task_id = result["task_ids"][0]

        # Test task list endpoint response time
        start_time = time.time()
        response = self.client.get(
            "/api/v1/documents/upload/tasks",
            params={"user_id": "test_user", "limit": 50}
        )
        elapsed_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 100, f"Task list API took {elapsed_ms:.2f}ms (target: <100ms)"
