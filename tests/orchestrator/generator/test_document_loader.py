"""Tests for document loading components.

This module provides comprehensive tests for the document loading, processing,
and validation components of the Arklex framework.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
import tempfile
import json
from pathlib import Path
from typing import Dict

import pytest
from unittest.mock import patch

from arklex.orchestrator.generator.docs.document_loader import DocumentLoader
from arklex.orchestrator.generator.docs.document_processor import DocumentProcessor
from arklex.orchestrator.generator.docs.document_validator import DocumentValidator


# --- Test Data ---


class NoReadTextPath(type(Path())):
    """Path subclass that raises AttributeError for read_text to test fallback logic."""

    def __getattribute__(self, name):
        if name == "read_text":
            raise AttributeError("no read_text")
        return super().__getattribute__(name)


@pytest.fixture
def sample_document() -> Dict:
    """Create a sample document for testing."""
    return {
        "title": "Product Creation Guide",
        "sections": [
            {
                "name": "Product Details",
                "content": "Required product information",
                "requirements": ["Name", "Description", "Price"],
            },
            {
                "name": "Pricing Guidelines",
                "content": "Pricing strategy guidelines",
                "requirements": ["Market research", "Profit margin"],
            },
        ],
        "metadata": {"version": "1.0", "last_updated": "2024-03-20"},
    }


@pytest.fixture
def sample_task_doc() -> Dict:
    """Create a sample task document for testing."""
    return {
        "task_id": "task1",
        "name": "Create Product",
        "description": "Create a new product in the store",
        "steps": [
            {
                "step_id": "step1",
                "description": "Enter product details",
                "required_fields": ["name", "description", "price"],
            },
            {
                "step_id": "step2",
                "description": "Set pricing strategy",
                "required_fields": ["market_price", "profit_margin"],
            },
        ],
    }


@pytest.fixture
def sample_instruction_doc() -> Dict:
    """Create a sample instruction document for testing."""
    return {
        "instruction_id": "inst1",
        "title": "Product Creation Instructions",
        "content": "Step-by-step guide for creating products",
        "sections": [
            {
                "section_id": "sec1",
                "title": "Product Information",
                "steps": ["Enter product name", "Add description", "Set price"],
            },
            {
                "section_id": "sec2",
                "title": "Pricing Strategy",
                "steps": ["Research market prices", "Calculate profit margin"],
            },
        ],
    }


# --- Fixtures ---


@pytest.fixture
def mock_file_system(sample_document: Dict):
    """Create a mock file system for testing."""
    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("pathlib.Path.read_text") as mock_read_text,
        patch("json.loads") as mock_json_loads,
    ):
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps(sample_document)
        mock_json_loads.return_value = sample_document

        yield {
            "exists": mock_exists,
            "read_text": mock_read_text,
            "json_loads": mock_json_loads,
        }


@pytest.fixture
def document_loader(mock_file_system) -> DocumentLoader:
    """Create a DocumentLoader instance for testing."""
    return DocumentLoader(cache_dir=Path("/tmp/cache"), validate_documents=True)


@pytest.fixture
def document_processor() -> DocumentProcessor:
    """Create a DocumentProcessor instance for testing."""
    return DocumentProcessor()


@pytest.fixture
def document_validator() -> DocumentValidator:
    """Create a DocumentValidator instance for testing."""
    return DocumentValidator()


# --- Test Classes ---


class TestDocumentLoader:
    """Test suite for the DocumentLoader class."""

    def test_load_document(
        self, document_loader: DocumentLoader, mock_file_system: Dict
    ) -> None:
        """Test loading a document from file."""
        doc_path = Path("/path/to/document.json")
        document = document_loader.load_document(doc_path)
        assert isinstance(document, dict)
        assert document["title"] == "Product Creation Guide"
        assert len(document["sections"]) == 2

    def test_load_task_document(
        self,
        document_loader: DocumentLoader,
        mock_file_system: Dict,
        sample_task_doc: Dict,
    ) -> None:
        """Test loading a task document."""
        doc_path = Path("/path/to/task.json")
        mock_file_system["json_loads"].return_value = sample_task_doc
        task_doc = document_loader.load_task_document(doc_path)
        assert isinstance(task_doc, dict)
        assert task_doc["task_id"] == "task1"
        assert len(task_doc["steps"]) == 2

    def test_load_instruction_document(
        self,
        document_loader: DocumentLoader,
        mock_file_system: Dict,
        sample_instruction_doc: Dict,
    ) -> None:
        """Test loading an instruction document."""
        doc_path = Path("/path/to/instruction.json")
        mock_file_system["json_loads"].return_value = sample_instruction_doc
        instruction_doc = document_loader.load_instruction_document(doc_path)
        assert isinstance(instruction_doc, dict)
        assert instruction_doc["instruction_id"] == "inst1"
        assert len(instruction_doc["sections"]) == 2

    def test_cache_document(self, document_loader, mock_file_system) -> None:
    def test_cache_document(
        self,
        document_loader: DocumentLoader,
        mock_file_system: Dict,
        sample_document: Dict,
    ) -> None:
        """Test document caching."""
        doc_path = Path("/path/to/document.json")
        document_loader.cache_document(doc_path, sample_document)
        cached_doc = document_loader.load_document(doc_path)
        assert cached_doc == sample_document

    def test_validate_document(
        self, document_loader: DocumentLoader, sample_document: Dict
    ) -> None:
        """Test document validation."""
        is_valid = document_loader.validate_document(sample_document)
        assert is_valid

    def test_load_document_file_not_found(self, document_loader) -> None:
        doc_path = Path("/not/found.json")
        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                document_loader.load_document(doc_path)

    def test_load_document_invalid_json(self, document_loader) -> None:
        doc_path = Path("/invalid.json")
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "read_text", return_value="not json"),
            patch("json.loads", side_effect=json.JSONDecodeError("msg", "doc", 0)),
        ):
            with pytest.raises(json.JSONDecodeError):
                document_loader.load_document(doc_path)

    def test_load_task_document_invalid_structure(
        self, document_loader, mock_file_system
    ) -> None:
        doc_path = Path("/invalid_task.json")
        mock_file_system["json_loads"].return_value = {"bad": "structure"}
        with pytest.raises(ValueError):
            document_loader.load_task_document(doc_path)

    def test_load_instruction_document_invalid_structure(
        self, document_loader, mock_file_system
    ) -> None:
        doc_path = Path("/invalid_instruction.json")
        mock_file_system["json_loads"].return_value = {"bad": "structure"}
        with pytest.raises(ValueError):
            document_loader.load_instruction_document(doc_path)

    def test_load_task_document_html_fallback(self, document_loader) -> None:
        doc_path = Path("/html_doc.html")
        html_content = "<html><head><title>Test</title></head><body><p>Step 1</p><p>Step 2</p></body></html>"
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "read_text", return_value=html_content),
            patch("json.loads", side_effect=json.JSONDecodeError("msg", "doc", 0)),
        ):
            doc = document_loader.load_task_document(doc_path)
            assert doc["name"] == "Test"
            assert len(doc["steps"]) == 2

    def test_load_task_document_url_handling(self, document_loader, tmp_path) -> None:
        """Test loading task document from URL."""
        url = "http://example.com/task.json"
        mock_response = MagicMock()
        mock_response.text = json.dumps(SAMPLE_TASK_DOC)
        mock_response.raise_for_status.return_value = None

        with (
            patch("requests.get", return_value=mock_response),
            patch.object(document_loader, "_validate_task_document", return_value=True),
        ):
            document_loader._cache[url] = SAMPLE_TASK_DOC
            doc = document_loader.load_task_document(url)
            assert doc["task_id"] == "task1"
            assert len(doc["steps"]) == 2

    def test_load_task_document_html_fallback_without_title(
        self, document_loader
    ) -> None:
        """Test HTML fallback when document has no title."""
        doc_path = Path("/html_doc.html")
        html_content = "<html><body><p>Step 1</p><p>Step 2</p></body></html>"
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "read_text", return_value=html_content),
            patch("json.loads", side_effect=json.JSONDecodeError("msg", "doc", 0)),
        ):
            doc = document_loader.load_task_document(doc_path)
            assert doc["name"] == "HTML Document"
            assert len(doc["steps"]) == 2

    def test_load_task_document_html_fallback_parsing_error(
        self, document_loader
    ) -> None:
        """Test HTML fallback when parsing fails."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html") as tmpfile:
            tmpfile.write("not html content")
            tmpfile.flush()
            tmp_path = NoReadTextPath(tmpfile.name)
        with (
            patch("json.loads", side_effect=json.JSONDecodeError("msg", "doc", 0)),
            patch(
                "arklex.orchestrator.generator.docs.document_loader.BeautifulSoup",
                side_effect=Exception("Parsing error"),
            ),
            patch.object(document_loader, "_validate_task_document", return_value=True),
        ):
            with pytest.raises(
                ValueError, match="neither valid JSON nor parseable HTML"
            ):
                document_loader.load_task_document(tmp_path)
        Path(tmpfile.name).unlink()

    def test_load_task_document_without_read_text_method(self) -> None:
        """Test loading task document when Path doesn't have read_text method."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmpfile:
            tmpfile.write(json.dumps(SAMPLE_TASK_DOC))
            tmpfile.flush()
            tmpfile.close()
            tmp_path = NoReadTextPath(tmpfile.name)
        loader = DocumentLoader(cache_dir=Path("/tmp/cache"), validate_documents=True)
        with patch.object(loader, "_validate_task_document", return_value=True):
            doc = loader.load_task_document(tmp_path)
            assert doc["task_id"] == SAMPLE_TASK_DOC["task_id"]
        Path(tmpfile.name).unlink()

    def test_load_instruction_document_without_read_text_method(self) -> None:
        """Test loading instruction document when Path doesn't have read_text method."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmpfile:
            tmpfile.write(json.dumps(SAMPLE_INSTRUCTION_DOC))
            tmpfile.flush()
            tmpfile.close()
            tmp_path = NoReadTextPath(tmpfile.name)
        loader = DocumentLoader(cache_dir=Path("/tmp/cache"), validate_documents=True)
        with patch.object(loader, "_validate_instruction_document", return_value=True):
            doc = loader.load_instruction_document(tmp_path)
            assert doc["instruction_id"] == SAMPLE_INSTRUCTION_DOC["instruction_id"]
        Path(tmpfile.name).unlink()

    def test_load_document_with_validation_disabled(self) -> None:
        """Test loading document with validation disabled."""
        loader = DocumentLoader(cache_dir=Path("/tmp/cache"), validate_documents=False)
        doc_path = Path("/invalid_structure.json")
        invalid_doc = {"invalid": "structure"}

        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "read_text", return_value=json.dumps(invalid_doc)),
        ):
            doc = loader.load_document(doc_path)
            assert doc == invalid_doc

    @pytest.mark.parametrize(
        "invalid_doc,expected",
        [
            ("not a dict", False),
            ({"title": "Test"}, False),
            ({"title": "Test", "sections": "not a list"}, False),
            ({"title": "Test", "sections": ["not a dict"]}, False),
            ({"title": "Test", "sections": [{"name": "Test"}]}, False),
            (
                {
                    "title": "Test",
                    "sections": [
                        {
                            "name": "Test",
                            "content": "Test",
                            "requirements": "not a list",
                        }
                    ],
                },
                False,
            ),
        ],
    )
    def test_validate_document_invalid_cases(
        self, document_loader, invalid_doc, expected
    ) -> None:
        """Test document validation with various invalid cases."""
        is_valid = document_loader.validate_document(invalid_doc)
        assert is_valid == expected

    @pytest.mark.parametrize(
        "invalid_doc,expected",
        [
            ("not a dict", False),
            ({"task_id": "test"}, False),
            (
                {
                    "task_id": "test",
                    "name": "test",
                    "description": "test",
                    "steps": "not a list",
                },
                False,
            ),
            (
                {
                    "task_id": "test",
                    "name": "test",
                    "description": "test",
                    "steps": ["not a dict"],
                },
                False,
            ),
            (
                {
                    "task_id": "test",
                    "name": "test",
                    "description": "test",
                    "steps": [{"step_id": "test"}],
                },
                False,
            ),
            (
                {
                    "task_id": "test",
                    "name": "test",
                    "description": "test",
                    "steps": [
                        {
                            "step_id": "test",
                            "description": "test",
                            "required_fields": "not a list",
                        }
                    ],
                },
                False,
            ),
        ],
    )
    def test_validate_task_document_invalid_cases(
        self, document_loader, invalid_doc, expected
    ) -> None:
        """Test task document validation with various invalid cases."""
        is_valid = document_loader._validate_task_document(invalid_doc)
        assert is_valid == expected

    @pytest.mark.parametrize(
        "invalid_doc,expected",
        [
            ("not a dict", False),
            ({"instruction_id": "test"}, False),
            (
                {
                    "instruction_id": "test",
                    "title": "test",
                    "content": "test",
                    "sections": "not a list",
                },
                False,
            ),
            (
                {
                    "instruction_id": "test",
                    "title": "test",
                    "content": "test",
                    "sections": ["not a dict"],
                },
                False,
            ),
            (
                {
                    "instruction_id": "test",
                    "title": "test",
                    "content": "test",
                    "sections": [{"section_id": "test"}],
                },
                False,
            ),
            (
                {
                    "instruction_id": "test",
                    "title": "test",
                    "content": "test",
                    "sections": [
                        {"section_id": "test", "title": "test", "steps": "not a list"}
                    ],
                },
                False,
            ),
        ],
    )
    def test_validate_instruction_document_invalid_cases(
        self, document_loader, invalid_doc, expected
    ) -> None:
        """Test instruction document validation with various invalid cases."""
        is_valid = document_loader._validate_instruction_document(invalid_doc)
        assert is_valid == expected


class TestDocumentProcessor:
    """Test suite for the DocumentProcessor class."""

    def test_process_document(
        self, document_processor: DocumentProcessor, sample_document: Dict
    ) -> None:
        """Test document processing."""
        processed_doc = document_processor.process_document(sample_document)
        assert isinstance(processed_doc, dict)
        assert "processed_sections" in processed_doc
        assert len(processed_doc["processed_sections"]) == 2

    def test_extract_requirements(
        self, document_processor: DocumentProcessor, sample_document: Dict
    ) -> None:
        """Test requirement extraction."""
        requirements = document_processor.extract_requirements(sample_document)
        assert isinstance(requirements, list)
        assert len(requirements) > 0
        assert all(isinstance(req, str) for req in requirements)

    def test_format_for_tasks(
        self, document_processor: DocumentProcessor, sample_document: Dict
    ) -> None:
        """Test document formatting for tasks."""
        formatted_doc = document_processor.format_for_tasks(sample_document)
        assert isinstance(formatted_doc, dict)
        assert "formatted_sections" in formatted_doc
        assert len(formatted_doc["formatted_sections"]) == 2

    def test_handle_specific_requirements(
        self, document_processor: DocumentProcessor
    ) -> None:
        """Test handling specific requirements."""
        requirements = ["Name", "Price", "Description"]
        handled_reqs = document_processor.handle_specific_requirements(requirements)
        assert isinstance(handled_reqs, list)
        assert len(handled_reqs) == len(requirements)


class TestDocumentValidator:
    """Test suite for the DocumentValidator class."""

    def test_validate_structure(
        self, document_validator: DocumentValidator, sample_document: Dict
    ) -> None:
        """Test document structure validation."""
        is_valid = document_validator.validate_structure(sample_document)
        assert is_valid

    def test_validate_required_fields(
        self, document_validator: DocumentValidator, sample_document: Dict
    ) -> None:
        """Test required fields validation."""
        is_valid = document_validator.validate_required_fields(sample_document)
        assert is_valid

    def test_validate_consistency(
        self, document_validator: DocumentValidator, sample_document: Dict
    ) -> None:
        """Test document consistency validation."""
        is_valid = document_validator.validate_consistency(sample_document)
        assert is_valid

    def test_get_error_messages(
        self, document_validator: DocumentValidator, sample_document: Dict
    ) -> None:
        """Test error message generation."""
        errors = document_validator.get_error_messages(sample_document)
        assert isinstance(errors, list)
        assert len(errors) == 0  # No errors in valid document


# --- Integration Tests ---


def test_integration_document_pipeline(
    mock_file_system: Dict, sample_document: Dict
) -> None:
    """Test the complete document handling pipeline integration."""
    # Initialize components
    document_loader = DocumentLoader(
        cache_dir=Path("/tmp/cache"), validate_documents=True
    )
    document_processor = DocumentProcessor()
    document_validator = DocumentValidator()

    # Load document
    doc_path = Path("/path/to/document.json")
    document = document_loader.load_document(doc_path)
    assert isinstance(document, dict)

    # Validate document
    is_valid = document_validator.validate_structure(document)
    assert is_valid

    # Process document
    processed_doc = document_processor.process_document(document)
    assert isinstance(processed_doc, dict)

    # Extract requirements
    requirements = document_processor.extract_requirements(processed_doc)
    assert isinstance(requirements, list)
    assert len(requirements) > 0

    # Format for tasks
    formatted_doc = document_processor.format_for_tasks(processed_doc)
    assert isinstance(formatted_doc, dict)
    assert "formatted_sections" in formatted_doc

    # Verify integration
    assert all("name" in section for section in formatted_doc["formatted_sections"])
    assert all("content" in section for section in formatted_doc["formatted_sections"])
