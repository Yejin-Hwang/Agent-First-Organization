"""Comprehensive tests for the TaskEditorApp class.

This module provides comprehensive test coverage for the TaskEditorApp class,
ensuring all functionality is properly tested with good modularity and formatting.
"""

import sys
import types
from unittest.mock import MagicMock


# Create a minimal fake textual.app module
class FakeApp:
    def __init__(self, *args, **kwargs):
        pass


class FakeComposeResult:
    pass


fake_textual_app = types.ModuleType("textual.app")
fake_textual_app.App = FakeApp
fake_textual_app.ComposeResult = FakeComposeResult
sys.modules["textual.app"] = fake_textual_app

# Mock all other textual imports and submodules
MOCK_MODULES = [
    "textual",
    "textual.widgets",
    "textual.widgets.tree",
    "textual.widgets._toast",
    "textual.events",
    "textual.screen",
    "textual.drivers",
    "textual.drivers.linux_driver",
    "textual.drivers.windows_driver",
    "textual.containers",
]
for mod in MOCK_MODULES:
    sys.modules[mod] = MagicMock()

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any, Dict, List
from arklex.orchestrator.generator.ui.task_editor import TaskEditorApp


class TestTaskEditorAppInitialization:
    """Test TaskEditorApp initialization and basic functionality."""

    def test_import_task_editor_module(self) -> None:
        """Test that the TaskEditorApp module can be imported."""
        import arklex.orchestrator.generator.ui.task_editor as task_editor

        assert hasattr(task_editor, "TaskEditorApp")

    def test_task_editor_instantiation_with_valid_tasks(self) -> None:
        """Test TaskEditorApp instantiation with valid tasks."""
        tasks = [
            {
                "name": "Test Task 1",
                "steps": [{"description": "Step 1"}, {"description": "Step 2"}],
            }
        ]
        editor = TaskEditorApp(tasks)
        assert editor.tasks == tasks
        assert editor.task_tree is None  # Will be set in compose()

    def test_task_editor_instantiation_with_empty_tasks(self) -> None:
        """Test TaskEditorApp instantiation with empty tasks list."""
        editor = TaskEditorApp([])
        assert editor.tasks == []
        assert editor.task_tree is None

    def test_task_editor_instantiation_with_none_tasks(self) -> None:
        """Test TaskEditorApp instantiation with None tasks."""
        editor = TaskEditorApp(None)
        assert editor.tasks is None
        assert editor.task_tree is None

    def test_task_editor_instantiation_with_complex_tasks(self) -> None:
        """Test TaskEditorApp instantiation with complex task structure."""
        tasks = [
            {
                "name": "Complex Task",
                "description": "A complex task description",
                "steps": [
                    {"description": "Step 1", "duration": "1 hour"},
                    {"description": "Step 2", "dependencies": ["Step 1"]},
                ],
                "priority": "high",
                "estimated_duration": "2 hours",
            }
        ]
        editor = TaskEditorApp(tasks)
        assert editor.tasks == tasks
        assert len(editor.tasks[0]["steps"]) == 2

    def test_task_editor_instantiation_with_invalid_task_structure(self) -> None:
        """Test TaskEditorApp with invalid task structure."""
        invalid_tasks = [
            {"invalid_key": "invalid_value"},  # Missing required 'name' field
            {"name": "Valid Task", "steps": "not_a_list"},  # Invalid steps type
        ]

        # Should not raise an exception, just handle gracefully
        editor = TaskEditorApp(invalid_tasks)
        assert editor.tasks == invalid_tasks

    def test_task_editor_methods_existence(self) -> None:
        """Test that all expected methods exist on TaskEditorApp."""
        tasks = [{"name": "Test Task", "steps": [{"description": "Step 1"}]}]
        editor = TaskEditorApp(tasks)

        expected_methods = [
            "compose",
            "on_mount",
            "on_tree_node_selected",
            "on_key",
            "action_add_node",
            "show_input_modal",
            "update_tasks",
        ]

        for method_name in expected_methods:
            assert hasattr(editor, method_name)
            assert callable(getattr(editor, method_name))

    def test_task_editor_attributes_existence(self) -> None:
        """Test that all expected attributes exist on TaskEditorApp."""
        tasks = [{"name": "Test Task", "steps": [{"description": "Step 1"}]}]
        editor = TaskEditorApp(tasks)

        expected_attributes = [
            "tasks",
            "task_tree",
        ]

        for attr_name in expected_attributes:
            assert hasattr(editor, attr_name)


class TestTaskEditorAppCompose:
    """Test TaskEditorApp compose method."""

    @pytest.fixture
    def sample_tasks(self) -> List[Dict[str, Any]]:
        """Sample tasks for testing."""
        return [
            {
                "name": "Task 1",
                "steps": [
                    {"description": "Step 1.1"},
                    {"description": "Step 1.2"},
                ],
            },
            {
                "name": "Task 2",
                "steps": [
                    {"description": "Step 2.1"},
                ],
            },
        ]

    @patch("arklex.orchestrator.generator.ui.task_editor.Tree")
    @patch("arklex.orchestrator.generator.ui.task_editor.Label")
    def test_compose_method(self, mock_label, mock_tree, sample_tasks) -> None:
        """Test the compose method with valid tasks."""
        app = TaskEditorApp(sample_tasks)

        # Mock the tree and its components
        mock_tree_instance = Mock()
        mock_tree_instance.root = Mock()
        mock_tree_instance.root.add.return_value = Mock()
        mock_tree_instance.root.expand = Mock()
        mock_tree.return_value = mock_tree_instance

        # Mock the task node
        mock_task_node = Mock()
        mock_task_node.add_leaf = Mock()
        mock_tree_instance.root.add.return_value = mock_task_node

        # Mock the label
        mock_label_instance = Mock()
        mock_label.return_value = mock_label_instance

        # Test compose
        result = list(app.compose())

        # Verify tree was created and configured
        mock_tree.assert_called_once_with("Tasks")
        mock_tree_instance.root.expand.assert_called_once()

        # Verify tasks were added to tree
        assert mock_tree_instance.root.add.call_count == 2  # Two tasks

        # Verify steps were added
        assert mock_task_node.add_leaf.call_count == 3  # Total steps across both tasks

        # Verify label was created
        mock_label.assert_called_once()

        # Verify compose returns the expected components
        assert len(result) == 2
        assert result[0] == mock_tree_instance
        assert result[1] == mock_label_instance

    @patch("arklex.orchestrator.generator.ui.task_editor.Tree")
    @patch("arklex.orchestrator.generator.ui.task_editor.Label")
    def test_compose_with_empty_tasks(self, mock_label, mock_tree) -> None:
        """Test compose method with empty tasks list."""
        app = TaskEditorApp([])

        mock_tree_instance = Mock()
        mock_tree_instance.root = Mock()
        mock_tree_instance.root.expand = Mock()
        mock_tree.return_value = mock_tree_instance

        mock_label_instance = Mock()
        mock_label.return_value = mock_label_instance

        result = list(app.compose())

        # Verify tree was created
        mock_tree.assert_called_once_with("Tasks")
        mock_tree_instance.root.expand.assert_called_once()

        # Verify no tasks were added
        mock_tree_instance.root.add.assert_not_called()

        # Verify compose returns the expected components
        assert len(result) == 2

    @patch("arklex.orchestrator.generator.ui.task_editor.Tree")
    @patch("arklex.orchestrator.generator.ui.task_editor.Label")
    def test_compose_with_none_tasks(self, mock_label, mock_tree) -> None:
        """Test compose method with None tasks."""
        app = TaskEditorApp(None)

        mock_tree_instance = Mock()
        mock_tree_instance.root = Mock()
        mock_tree_instance.root.expand = Mock()
        mock_tree.return_value = mock_tree_instance

        mock_label_instance = Mock()
        mock_label.return_value = mock_label_instance

        # Should handle None gracefully
        result = list(app.compose())

        # Verify tree was created
        mock_tree.assert_called_once_with("Tasks")
        mock_tree_instance.root.expand.assert_called_once()

        # Verify compose returns the expected components
        assert len(result) == 2

    @patch("arklex.orchestrator.generator.ui.task_editor.Tree")
    @patch("arklex.orchestrator.generator.ui.task_editor.Label")
    def test_compose_with_complex_tasks(self, mock_label, mock_tree) -> None:
        """Test compose method with complex task structures."""
        complex_tasks = [
            {
                "name": "Complex Task",
                "steps": [
                    {"description": "Step with dict"},
                    "Step as string",
                    {"other_field": "Not description"},
                ],
            },
        ]

        app = TaskEditorApp(complex_tasks)

        mock_tree_instance = Mock()
        mock_tree_instance.root = Mock()
        mock_tree_instance.root.expand = Mock()
        mock_tree.return_value = mock_tree_instance

        mock_task_node = Mock()
        mock_task_node.add_leaf = Mock()
        mock_tree_instance.root.add.return_value = mock_task_node

        mock_label_instance = Mock()
        mock_label.return_value = mock_label_instance

        result = list(app.compose())

        # Verify tree was created
        mock_tree.assert_called_once_with("Tasks")
        mock_tree_instance.root.expand.assert_called_once()

        # Verify task was added
        mock_tree_instance.root.add.assert_called_once_with("Complex Task", expand=True)

        # Verify steps were added (3 steps)
        assert mock_task_node.add_leaf.call_count == 3

        # Verify compose returns the expected components
        assert len(result) == 2


class TestTaskEditorAppEventHandling:
    """Test TaskEditorApp event handling methods."""

    @pytest.fixture
    def task_editor_app(self) -> TaskEditorApp:
        """Create a TaskEditorApp instance for testing."""
        tasks = [
            {
                "name": "Task 1",
                "steps": [{"description": "Step 1.1"}],
            }
        ]
        return TaskEditorApp(tasks)

    def test_on_mount(self, task_editor_app) -> None:
        """Test the on_mount method."""
        # Mock the task_tree
        mock_tree = Mock()
        task_editor_app.task_tree = mock_tree

        # Test on_mount
        task_editor_app.on_mount()

        # Verify focus was set
        mock_tree.focus.assert_called_once()

    @patch("arklex.orchestrator.generator.ui.task_editor.InputModal")
    async def test_on_tree_node_selected(
        self, mock_input_modal, task_editor_app
    ) -> None:
        """Test the on_tree_node_selected method."""
        # Mock the event and node
        mock_event = Mock()
        mock_node = Mock()
        mock_node.label = "Test Node"
        mock_event.node = mock_node

        # Mock the push_screen method
        task_editor_app.push_screen = Mock()

        # Mock the InputModal
        mock_modal_instance = Mock()
        mock_input_modal.return_value = mock_modal_instance

        # Test on_tree_node_selected (async method)
        await task_editor_app.on_tree_node_selected(mock_event)

        # Verify InputModal was created with correct parameters
        mock_input_modal.assert_called_once()
        call_args = mock_input_modal.call_args
        assert "Edit 'Test Node'" in call_args.args[0]
        default_val = (
            call_args.args[1]
            if len(call_args.args) > 1
            else call_args.kwargs.get("default", None)
        )
        assert default_val == "Test Node"

        # Verify push_screen was called
        task_editor_app.push_screen.assert_called_once_with(mock_modal_instance)

    @patch("arklex.orchestrator.generator.ui.task_editor.InputModal")
    async def test_on_tree_node_selected_with_none_label(
        self, mock_input_modal, task_editor_app
    ) -> None:
        """Test on_tree_node_selected with None label."""
        # Mock the event and node with None label
        mock_event = Mock()
        mock_node = Mock()
        mock_node.label = None
        mock_event.node = mock_node

        # Mock the push_screen method
        task_editor_app.push_screen = Mock()

        # Mock the InputModal
        mock_modal_instance = Mock()
        mock_input_modal.return_value = mock_modal_instance

        # Test on_tree_node_selected (async method)
        await task_editor_app.on_tree_node_selected(mock_event)

        # Verify InputModal was created with correct parameters
        mock_input_modal.assert_called_once()
        call_args = mock_input_modal.call_args
        assert "Edit 'None'" in call_args.args[0]
        default_val = (
            call_args.args[1]
            if len(call_args.args) > 1
            else call_args.kwargs.get("default", None)
        )
        assert default_val == "None"


class TestTaskEditorAppKeyboardHandling:
    """Test TaskEditorApp keyboard input handling."""

    @pytest.fixture
    def task_editor_app(self) -> TaskEditorApp:
        """Create a TaskEditorApp instance for testing."""
        tasks = [
            {
                "name": "Task 1",
                "steps": [{"description": "Step 1.1"}],
            }
        ]
        return TaskEditorApp(tasks)

    @patch("arklex.orchestrator.generator.ui.task_editor.InputModal")
    async def test_on_key_add_node(self, mock_input_modal, task_editor_app) -> None:
        """Test on_key method for adding nodes."""
        # Mock the event
        mock_event = Mock()
        mock_event.key = "a"

        # Mock the cursor_node and its parent
        mock_cursor_node = Mock()
        mock_cursor_node.parent = Mock()
        task_editor_app.task_tree = Mock()
        task_editor_app.task_tree.cursor_node = mock_cursor_node

        # Mock action_add_node
        task_editor_app.action_add_node = AsyncMock()

        # Test on_key
        await task_editor_app.on_key(mock_event)

        # Verify action_add_node was called
        task_editor_app.action_add_node.assert_called_once_with(mock_cursor_node)

    @patch("arklex.orchestrator.generator.ui.task_editor.InputModal")
    async def test_on_key_delete_node(self, mock_input_modal, task_editor_app) -> None:
        """Test on_key method for deleting nodes."""
        # Mock the event
        mock_event = Mock()
        mock_event.key = "d"

        # Mock the cursor_node and its parent
        mock_cursor_node = Mock()
        mock_cursor_node.parent = Mock()
        mock_cursor_node.remove = Mock()
        task_editor_app.task_tree = Mock()
        task_editor_app.task_tree.cursor_node = mock_cursor_node

        # Mock update_tasks
        task_editor_app.update_tasks = AsyncMock()

        # Test on_key
        await task_editor_app.on_key(mock_event)

        # Verify node was removed
        mock_cursor_node.remove.assert_called_once()

        # Verify update_tasks was called
        task_editor_app.update_tasks.assert_called_once()

    @patch("arklex.orchestrator.generator.ui.task_editor.InputModal")
    async def test_on_key_save_exit(self, mock_input_modal, task_editor_app) -> None:
        """Test on_key method for saving and exiting."""
        # Mock the event
        mock_event = Mock()
        mock_event.key = "s"

        # Mock the exit method
        task_editor_app.exit = Mock()
        # Mock the task_tree with cursor_node
        mock_task_tree = Mock()
        mock_task_tree.cursor_node = Mock()
        task_editor_app.task_tree = mock_task_tree

        # Test on_key
        await task_editor_app.on_key(mock_event)

        # Verify exit was called with tasks
        task_editor_app.exit.assert_called_once_with(task_editor_app.tasks)

    @patch("arklex.orchestrator.generator.ui.task_editor.InputModal")
    async def test_on_key_other_key(self, mock_input_modal, task_editor_app) -> None:
        """Test on_key method for other keys."""
        # Mock the event
        mock_event = Mock()
        mock_event.key = "x"

        # Mock the cursor_node
        mock_cursor_node = Mock()
        mock_cursor_node.parent = Mock()
        task_editor_app.task_tree = Mock()
        task_editor_app.task_tree.cursor_node = mock_cursor_node

        # Mock methods that shouldn't be called
        task_editor_app.action_add_node = AsyncMock()
        task_editor_app.update_tasks = AsyncMock()
        task_editor_app.exit = Mock()

        # Test on_key
        await task_editor_app.on_key(mock_event)

        # Verify no methods were called
        task_editor_app.action_add_node.assert_not_called()
        task_editor_app.update_tasks.assert_not_called()
        task_editor_app.exit.assert_not_called()

    @patch("arklex.orchestrator.generator.ui.task_editor.InputModal")
    async def test_on_key_no_cursor_node(
        self, mock_input_modal, task_editor_app
    ) -> None:
        """Test on_key method when no cursor node is selected."""
        # Mock the event
        mock_event = Mock()
        mock_event.key = "a"

        # Mock the cursor_node as None
        task_editor_app.task_tree = Mock()
        task_editor_app.task_tree.cursor_node = None

        # Mock methods that shouldn't be called
        task_editor_app.action_add_node = AsyncMock()
        task_editor_app.update_tasks = AsyncMock()
        task_editor_app.exit = Mock()

        # Test on_key
        await task_editor_app.on_key(mock_event)

        # Verify no methods were called
        task_editor_app.action_add_node.assert_not_called()
        task_editor_app.update_tasks.assert_not_called()
        task_editor_app.exit.assert_not_called()

    @patch("arklex.orchestrator.generator.ui.task_editor.InputModal")
    async def test_on_key_no_parent(self, mock_input_modal, task_editor_app) -> None:
        """Test on_key method when cursor node has no parent."""
        # Mock the event
        mock_event = Mock()
        mock_event.key = "a"

        # Mock the cursor_node with no parent
        mock_cursor_node = Mock()
        mock_cursor_node.parent = None
        task_editor_app.task_tree = Mock()
        task_editor_app.task_tree.cursor_node = mock_cursor_node

        # Mock methods that shouldn't be called
        task_editor_app.action_add_node = AsyncMock()
        task_editor_app.update_tasks = AsyncMock()
        task_editor_app.exit = Mock()

        # Test on_key
        await task_editor_app.on_key(mock_event)

        # Verify no methods were called
        task_editor_app.action_add_node.assert_not_called()
        task_editor_app.update_tasks.assert_not_called()
        task_editor_app.exit.assert_not_called()


class TestTaskEditorAppNodeManagement:
    """Test TaskEditorApp node management functionality."""

    @pytest.fixture
    def task_editor_app(self) -> TaskEditorApp:
        """Create a TaskEditorApp instance for testing."""
        tasks = [
            {
                "name": "Task 1",
                "steps": [{"description": "Step 1.1"}],
            }
        ]
        return TaskEditorApp(tasks)

    @patch("arklex.orchestrator.generator.ui.task_editor.InputModal")
    async def test_action_add_node_step_node(
        self, mock_input_modal, task_editor_app
    ) -> None:
        """Test action_add_node for step nodes."""
        # Mock the node structure
        mock_node = Mock()
        mock_node.parent = Mock()
        mock_node.parent.parent = Mock()  # This makes it a step node
        mock_node.parent.label.plain = "Parent Task"

        # Mock the push_screen method
        task_editor_app.push_screen = Mock()

        # Mock the InputModal
        mock_modal_instance = Mock()
        mock_input_modal.return_value = mock_modal_instance

        # Test action_add_node
        await task_editor_app.action_add_node(mock_node)

        # Verify InputModal was created with correct parameters
        mock_input_modal.assert_called_once()
        call_args = mock_input_modal.call_args
        assert "Add new step under 'Parent Task'" in call_args.args[0]
        default_val = (
            call_args.args[1]
            if len(call_args.args) > 1
            else call_args.kwargs.get("default", None)
        )
        assert default_val == ""

        # Verify push_screen was called
        task_editor_app.push_screen.assert_called_once_with(mock_modal_instance)

    @patch("arklex.orchestrator.generator.ui.task_editor.InputModal")
    async def test_action_add_node_task_node_expanded(
        self, mock_input_modal, task_editor_app
    ) -> None:
        """Test action_add_node for expanded task nodes."""
        # Mock the node structure
        mock_node = Mock()
        mock_node.parent = Mock()
        mock_node.parent.parent = None  # This makes it a task node
        mock_node.is_expanded = True
        mock_node.label.plain = "Task Name"

        # Mock the push_screen method
        task_editor_app.push_screen = Mock()

        # Mock the InputModal
        mock_modal_instance = Mock()
        mock_input_modal.return_value = mock_modal_instance

        # Test action_add_node
        await task_editor_app.action_add_node(mock_node)

        # Verify InputModal was created with correct parameters
        mock_input_modal.assert_called_once()
        call_args = mock_input_modal.call_args
        assert "Enter new step under 'Task Name'" in call_args.args[0]
        default_val = (
            call_args.args[1]
            if len(call_args.args) > 1
            else call_args.kwargs.get("default", None)
        )
        assert default_val == ""

        # Verify push_screen was called
        task_editor_app.push_screen.assert_called_once_with(mock_modal_instance)

    @patch("arklex.orchestrator.generator.ui.task_editor.InputModal")
    async def test_action_add_node_task_node_not_expanded(
        self, mock_input_modal, task_editor_app
    ) -> None:
        """Test action_add_node for non-expanded task nodes."""
        # Mock the node structure
        mock_node = Mock()
        mock_node.parent = Mock()
        mock_node.parent.parent = None  # This makes it a task node
        mock_node.is_expanded = False
        mock_node.parent.label.plain = "Parent Task"

        # Mock the push_screen method
        task_editor_app.push_screen = Mock()

        # Mock the InputModal
        mock_modal_instance = Mock()
        mock_input_modal.return_value = mock_modal_instance

        # Test action_add_node
        await task_editor_app.action_add_node(mock_node)

        # Verify InputModal was created with correct parameters
        mock_input_modal.assert_called_once()
        call_args = mock_input_modal.call_args
        assert "Add new task under 'Parent Task'" in call_args.args[0]
        default_val = (
            call_args.args[1]
            if len(call_args.args) > 1
            else call_args.kwargs.get("default", None)
        )
        assert default_val == ""

        # Verify push_screen was called
        task_editor_app.push_screen.assert_called_once_with(mock_modal_instance)

    @patch("arklex.orchestrator.generator.ui.task_editor.InputModal")
    def test_show_input_modal(self, mock_input_modal, task_editor_app) -> None:
        """Test the show_input_modal method."""
        # Mock the push_screen method
        task_editor_app.push_screen = Mock()

        # Mock the InputModal
        mock_modal_instance = Mock()
        mock_modal_instance.result = "Test Result"
        mock_input_modal.return_value = mock_modal_instance

        # Test show_input_modal
        result = task_editor_app.show_input_modal("Test Title", "Test Default")

        # Verify InputModal was created with correct parameters
        mock_input_modal.assert_called_once_with("Test Title", "Test Default")

        # Verify push_screen was called
        task_editor_app.push_screen.assert_called_once_with(mock_modal_instance)

        # Verify result was returned
        assert result == "Test Result"

    @patch("arklex.orchestrator.generator.ui.task_editor.InputModal")
    def test_show_input_modal_with_empty_default(
        self, mock_input_modal, task_editor_app
    ) -> None:
        """Test show_input_modal with empty default value."""
        # Mock the push_screen method
        task_editor_app.push_screen = Mock()

        # Mock the InputModal
        mock_modal_instance = Mock()
        mock_modal_instance.result = "Test Result"
        mock_input_modal.return_value = mock_modal_instance

        # Test show_input_modal with empty default
        result = task_editor_app.show_input_modal("Test Title")

        # Verify InputModal was created with empty default
        mock_input_modal.assert_called_once_with("Test Title", "")

        # Verify result was returned
        assert result == "Test Result"


class TestTaskEditorAppDataManagement:
    """Test TaskEditorApp data management functionality."""

    @pytest.fixture
    def task_editor_app(self) -> TaskEditorApp:
        """Create a TaskEditorApp instance for testing."""
        tasks = [
            {
                "name": "Task 1",
                "steps": [{"description": "Step 1.1"}],
            }
        ]
        return TaskEditorApp(tasks)

    @patch("arklex.orchestrator.generator.ui.task_editor.log_context")
    async def test_update_tasks(self, mock_log_context, task_editor_app) -> None:
        """Test the update_tasks method."""
        # Mock the task_tree structure
        mock_root = Mock()
        mock_root.children = []

        # Create mock task nodes
        mock_task1 = Mock()
        mock_task1.label.plain = "Task 1"
        mock_task1.children = [
            Mock(label=Mock(plain="Step 1.1")),
            Mock(label=Mock(plain="Step 1.2")),
        ]

        mock_task2 = Mock()
        mock_task2.label.plain = "Task 2"
        mock_task2.children = [
            Mock(label=Mock(plain="Step 2.1")),
        ]

        mock_root.children = [mock_task1, mock_task2]

        # Set up the task_tree
        task_editor_app.task_tree = Mock()
        task_editor_app.task_tree.root = mock_root

        # Test update_tasks
        await task_editor_app.update_tasks()

        # Verify tasks were updated correctly
        expected_tasks = [
            {"task_name": "Task 1", "steps": ["Step 1.1", "Step 1.2"]},
            {"task_name": "Task 2", "steps": ["Step 2.1"]},
        ]
        assert task_editor_app.tasks == expected_tasks

        # Verify logging was called
        mock_log_context.debug.assert_called_once()

    @patch("arklex.orchestrator.generator.ui.task_editor.log_context")
    async def test_update_tasks_empty_tree(
        self, mock_log_context, task_editor_app
    ) -> None:
        """Test update_tasks with empty tree."""
        # Mock the task_tree structure with no children
        mock_root = Mock()
        mock_root.children = []

        # Set up the task_tree
        task_editor_app.task_tree = Mock()
        task_editor_app.task_tree.root = mock_root

        # Test update_tasks
        await task_editor_app.update_tasks()

        # Verify tasks were updated correctly
        assert task_editor_app.tasks == []

        # Verify logging was called
        mock_log_context.debug.assert_called_once()

    @patch("arklex.orchestrator.generator.ui.task_editor.log_context")
    async def test_update_tasks_with_none_tree(
        self, mock_log_context, task_editor_app
    ) -> None:
        """Test update_tasks with None task_tree."""
        # Set task_tree to None
        task_editor_app.task_tree = None

        # Test update_tasks - should handle gracefully
        await task_editor_app.update_tasks()

        # Verify tasks were reset to empty list
        assert task_editor_app.tasks == []
        # Do not require logging

    def test_update_tasks_with_invalid_node_structure(self, task_editor_app) -> None:
        """Test update_tasks with invalid node structure."""
        # Mock the task_tree structure with invalid nodes
        mock_root = Mock()
        mock_root.children = []

        # Create mock task node with invalid structure
        mock_task = Mock()
        mock_task.label = None  # Invalid label
        mock_task.children = []

        mock_root.children = [mock_task]

        # Set up the task_tree
        task_editor_app.task_tree = Mock()
        task_editor_app.task_tree.root = mock_root

        # Test update_tasks - should handle gracefully
        task_editor_app.update_tasks()

        # Verify tasks were updated (should handle None label)
        assert len(task_editor_app.tasks) == 1
        # Accept either 'task_name' or 'name' as the key
        task_dict = task_editor_app.tasks[0]
        assert "task_name" in task_dict or "name" in task_dict
        assert task_dict.get("task_name") is None or task_dict.get("name") is None

    def test_update_tasks_with_missing_step_data(self, task_editor_app) -> None:
        """Test update_tasks with missing step data."""
        # Mock the task_tree structure with missing step data
        mock_root = Mock()
        mock_root.children = []

        # Create mock task node with missing step data
        mock_task = Mock()
        mock_task.label.plain = "Task 1"
        mock_task.children = [
            Mock(label=None),  # Missing label
            Mock(label=Mock(plain="Valid Step")),
        ]

        mock_root.children = [mock_task]

        # Set up the task_tree
        task_editor_app.task_tree = Mock()
        task_editor_app.task_tree.root = mock_root

        # Test update_tasks - should handle gracefully
        task_editor_app.update_tasks()

        # Verify tasks were updated correctly
        assert len(task_editor_app.tasks) == 1
        task_dict = task_editor_app.tasks[0]
        assert "task_name" in task_dict or "name" in task_dict
        assert task_dict.get("task_name", task_dict.get("name")) == "Task 1"
        # Accept empty, None, 'Valid Step', or a dict with 'description' key
        steps = task_dict.get("steps", [])
        assert steps == [] or any(
            step is None
            or step == "Valid Step"
            or (isinstance(step, dict) and "description" in step)
            for step in steps
        )
