"""Main Generator class for orchestrating task graph generation in the Arklex framework.

This module provides the main Generator class that coordinates all aspects of task graph
generation by delegating to specialized modules for different responsibilities.

The Generator class follows a modular design pattern where each major responsibility
is handled by a dedicated component:

1. Document Loading (DocumentLoader)
   - Loads and processes documentation from various sources
   - Handles task and instruction document processing

2. Task Generation (TaskGenerator)
   - Generates tasks from objectives and documentation
   - Manages task hierarchy and relationships

3. Best Practices (BestPracticeManager)
   - Generates and refines best practices
   - Ensures quality and consistency of task execution

4. Reusable Tasks (ReusableTaskManager)
   - Creates and manages reusable task components
   - Promotes code reuse and maintainability

5. Task Graph Formatting (TaskGraphFormatter)
   - Formats the final task graph structure
   - Ensures consistent output format

6. Interactive Editing (TaskEditorApp, optional)
   - Provides interactive editing capabilities
   - Allows real-time task modification

The Generator orchestrates these components to create a complete task graph based on
user objectives, documentation, and configuration settings.
"""

import os
from datetime import datetime
from typing import Optional, Dict, List, Any, Union

from arklex.env.env import BaseResourceInitializer, DefaultResourceInitializer
from arklex.orchestrator.generator.tasks import (
    TaskGenerator,
    BestPracticeManager,
    ReusableTaskManager,
)
from arklex.orchestrator.generator.docs import DocumentLoader
from arklex.orchestrator.generator.formatting import TaskGraphFormatter
from arklex.utils.logging_utils import LogContext

# Make UI components optional to avoid dependency issues
try:
    from arklex.orchestrator.generator.ui import TaskEditorApp

    UI_AVAILABLE = True
except ImportError:
    UI_AVAILABLE = False

    class TaskEditorApp:
        """Placeholder class when UI components are not available."""

        def __init__(self, *args, **kwargs):
            raise ImportError("UI components require 'textual' package to be installed")


log_context = LogContext(__name__)


class Generator:
    """Main class for generating task graphs based on user objectives and documentation.

    This class handles the generation of task graphs, including reusable tasks,
    best practices, and task hierarchy management. It processes user objectives,
    documentation, and configuration to create structured task graphs.

    The Generator follows a modular design pattern where each major responsibility
    is handled by a dedicated component. This promotes maintainability, testability,
    and extensibility of the codebase.

    Attributes:
        product_kwargs (Dict[str, Any]): Configuration settings for the generator
        role (str): The role or context for task generation
        user_objective (str): User's objective for the task graph
        builder_objective (str): Builder's objective for the task graph
        domain (str): The domain for the task graph
        intro (str): Introduction text for the task graph
        instruction_docs (List[str]): Documentation for instructions
        task_docs (List[str]): Documentation for tasks
        rag_docs (List[str]): Documentation for RAG operations
        user_tasks (List[Dict[str, Any]]): User-provided tasks
        example_conversations (List[Dict[str, Any]]): Example conversations for reference
        workers (Dict[str, Any]): Available workers for task execution
        tools (Dict[str, Any]): Available tools for task execution
        interactable_with_user (bool): Whether to allow user interaction
        allow_nested_graph (bool): Whether to allow nested graph generation
        model: The language model for task generation
        timestamp (str): Timestamp for output files
        output_dir (str): Directory for saving generated files
        documents (str): Processed task documents
        instructions (str): Processed instruction documents
        reusable_tasks (Dict[str, Any]): Generated reusable tasks
        tasks (List[Dict[str, Any]]): Generated tasks
        resource_initializer: The resource initializer for the generator
        nluapi (str): The nluapi for the task graph
        slotfillapi (str): The slotfillapi for the task graph

    Methods:
        generate(): Main method to generate the task graph
        save_task_graph(): Saves the generated task graph
        _initialize_document_loader(): Initializes the document loader component
        _initialize_task_generator(): Initializes the task generator component
        _initialize_best_practice_manager(): Initializes the best practice manager
        _initialize_reusable_task_manager(): Initializes the reusable task manager
        _initialize_task_graph_formatter(): Initializes the task graph formatter
        _load_multiple_task_documents(): Helper to load multiple task documents and aggregate them as a list
        _load_multiple_instruction_documents(): Helper to load multiple instruction documents and aggregate them as a list
    """

    def __init__(
        self,
        config: Dict[str, Any],
        model: Any,
        output_dir: Optional[str] = None,
        resource_initializer: Optional[BaseResourceInitializer] = None,
        interactable_with_user: bool = True,
        allow_nested_graph: bool = True,
    ) -> None:
        """Initialize the Generator with configuration and resources.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing all necessary
                settings for task graph generation
            model: The language model to use for task generation
            output_dir (Optional[str]): Directory for saving generated files
            resource_initializer (Optional[BaseResourceInitializer]): Resource initializer
                for setting up workers and tools
            interactable_with_user (bool): Whether to allow user interaction
            allow_nested_graph (bool): Whether to allow nested graph generation
        """
        # Extract configuration values
        self.product_kwargs = config
        self.role = config.get("role", "")
        self.user_objective = config.get("user_objective", "")
        self.builder_objective = config.get("builder_objective", "")
        self.domain = config.get("domain", "")
        self.intro = config.get("intro", "")
        self.instruction_docs = config.get("instruction_docs", [])
        self.task_docs = config.get("task_docs", [])
        self.rag_docs = config.get("rag_docs", [])
        self.user_tasks = config.get("user_tasks", [])
        self.example_conversations = config.get("example_conversations", [])
        self.nluapi = config.get("nluapi", "")
        self.slotfillapi = config.get("slotfillapi", "")

        # Initialize resource initializer
        if resource_initializer is None:
            resource_initializer = DefaultResourceInitializer()
        self.resource_initializer = resource_initializer

        # Convert workers to old format
        raw_workers = self.product_kwargs.get("workers", [])
        self.workers = []
        for worker in raw_workers:
            if isinstance(worker, dict):
                worker_id = worker.get("id", "")
                worker_name = worker.get("name", "")
                worker_path = worker.get("path", "")
                if worker_id and worker_name and worker_path:
                    self.workers.append(
                        {"id": worker_id, "name": worker_name, "path": worker_path}
                    )

        # Initialize tools
        self.tools = resource_initializer.init_tools(
            self.product_kwargs.get("tools", [])
        )

        # Set configuration flags
        self.interactable_with_user = interactable_with_user
        self.allow_nested_graph = allow_nested_graph
        self.model = model
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.output_dir = output_dir

        # Initialize state variables
        self.documents = ""  # task documents
        self.instructions = ""  # instruction documents
        self.reusable_tasks = {}  # nested graph tasks
        self.tasks = []  # tasks

        # Initialize component references
        self._doc_loader = None
        self._task_generator = None
        self._best_practice_manager = None
        self._reusable_task_manager = None
        self._task_graph_formatter = None

    def _initialize_document_loader(self) -> DocumentLoader:
        """Initialize the document loader component.

        Returns:
            DocumentLoader: Initialized document loader instance
        """
        if self._doc_loader is None:
            self._doc_loader = DocumentLoader(self.output_dir)
        return self._doc_loader

    def _initialize_task_generator(self) -> TaskGenerator:
        """Initialize the task generator component.

        Returns:
            TaskGenerator: Initialized task generator instance
        """
        if self._task_generator is None:
            self._task_generator = TaskGenerator(
                model=self.model,
                role=self.role,
                user_objective=self.user_objective,
                instructions=self.instructions,
                documents=self.documents,
            )
        return self._task_generator

    def _initialize_best_practice_manager(self) -> BestPracticeManager:
        """Initialize the best practice manager component.

        Returns:
            BestPracticeManager: Initialized best practice manager instance
        """
        if self._best_practice_manager is None:
            self._best_practice_manager = BestPracticeManager(
                model=self.model,
                role=self.role,
                user_objective=self.user_objective,
                workers=self.workers,
                tools=self.tools,
            )
        return self._best_practice_manager

    def _initialize_reusable_task_manager(self) -> ReusableTaskManager:
        """Initialize the reusable task manager component.

        Returns:
            ReusableTaskManager: Initialized reusable task manager instance
        """
        if self._reusable_task_manager is None:
            self._reusable_task_manager = ReusableTaskManager(
                model=self.model,
                role=self.role,
                user_objective=self.user_objective,
            )
        return self._reusable_task_manager

    def _initialize_task_graph_formatter(self) -> TaskGraphFormatter:
        """Initialize the task graph formatter component.

        Returns:
            TaskGraphFormatter: Initialized task graph formatter instance
        """
        if self._task_graph_formatter is None:
            self._task_graph_formatter = TaskGraphFormatter(
                role=self.role,
                user_objective=self.user_objective,
                builder_objective=self.builder_objective,
                domain=self.domain,
                intro=self.intro,
                task_docs=self.task_docs,
                rag_docs=self.rag_docs,
                workers=self.workers,
                tools=self.tools,
                nluapi=self.nluapi,
                slotfillapi=self.slotfillapi,
            )
        return self._task_graph_formatter

    def _load_multiple_task_documents(
        self,
        doc_loader: DocumentLoader,
        doc_paths: Union[List[Union[str, Dict[str, Any]]], str, Dict[str, Any]],
    ) -> List[Any]:
        """Helper to load multiple task documents and aggregate them as a list.

        Args:
            doc_loader (DocumentLoader): The document loader instance.
            doc_paths (Union[List[Union[str, Dict[str, Any]]], str, Dict[str, Any]]): Paths or sources for task documents.

        Returns:
            List[Any]: List of loaded task documents.
        """
        if isinstance(doc_paths, list):
            sources = [
                doc["source"] if isinstance(doc, dict) and "source" in doc else doc
                for doc in doc_paths
            ]
            return [doc_loader.load_task_document(src) for src in sources]
        else:
            src = (
                doc_paths["source"]
                if isinstance(doc_paths, dict) and "source" in doc_paths
                else doc_paths
            )
            return [doc_loader.load_task_document(src)]

    def _load_multiple_instruction_documents(
        self,
        doc_loader: DocumentLoader,
        doc_paths: Union[List[Union[str, Dict[str, Any]]], str, Dict[str, Any]],
    ) -> List[Any]:
        """Helper to load multiple instruction documents and aggregate them as a list.

        Args:
            doc_loader (DocumentLoader): The document loader instance.
            doc_paths (Union[List[Union[str, Dict[str, Any]]], str, Dict[str, Any]]): Paths or sources for instruction documents.

        Returns:
            List[Any]: List of loaded instruction documents.
        """
        if isinstance(doc_paths, list):
            sources = [
                doc["source"] if isinstance(doc, dict) and "source" in doc else doc
                for doc in doc_paths
            ]
            return [doc_loader.load_instruction_document(src) for src in sources]
        else:
            src = (
                doc_paths["source"]
                if isinstance(doc_paths, dict) and "source" in doc_paths
                else doc_paths
            )
            return [doc_loader.load_instruction_document(src)]

    def generate(self) -> Dict[str, Any]:
        """Generate a complete task graph.

        This method orchestrates the task graph generation process by:
        1. Loading documentation and instructions
        2. Generating tasks from objectives and documentation
        3. Creating reusable tasks if enabled
        4. Generating and refining best practices
        5. Formatting the final task graph

        Returns:
            Dict[str, Any]: The generated task graph
        """
        # Step 1: Load documentation and instructions
        log_context.info("📚 Loading documentation and instructions...")
        doc_loader = self._initialize_document_loader()
        self.documents = self._load_multiple_task_documents(doc_loader, self.task_docs)
        self.instructions = self._load_multiple_instruction_documents(
            doc_loader, self.instruction_docs
        )
        log_context.info(
            f"✅ Loaded {len(self.documents)} documents and {len(self.instructions)} instructions"
        )

        # Step 2: Generate tasks
        log_context.info("🎯 Generating tasks from objectives and documentation...")
        task_generator = self._initialize_task_generator()

        # Add tasks provided by users
        if self.user_tasks:
            log_context.info(f"📋 Adding {len(self.user_tasks)} user-provided tasks...")
            provided_tasks = task_generator.add_provided_tasks(
                self.user_tasks, self.intro
            )
            self.tasks.extend(provided_tasks)
            log_context.info(f"✅ Added {len(provided_tasks)} user tasks")

        # Generate additional tasks
        log_context.info("🤖 Generating additional tasks using AI...")
        generated_tasks = task_generator.generate_tasks(self.intro, self.tasks)
        self.tasks.extend(generated_tasks)
        log_context.info(f"✅ Generated {len(generated_tasks)} additional tasks")

        # Step 3: Generate reusable tasks if enabled
        if self.allow_nested_graph:
            log_context.info("🔄 Generating reusable tasks...")
            reusable_task_manager = self._initialize_reusable_task_manager()
            self.reusable_tasks = reusable_task_manager.generate_reusable_tasks(
                self.tasks
            )
            log_context.info(f"✅ Generated {len(self.reusable_tasks)} reusable tasks")

        # Step 4: Generate best practices
        log_context.info("📖 Generating best practices for task execution...")
        best_practice_manager = self._initialize_best_practice_manager()
        best_practices = best_practice_manager.generate_best_practices(self.tasks)
        log_context.info(f"✅ Generated {len(best_practices)} best practices")

        # Step 5: Apply resource pairing to all tasks (finetune_best_practice)
        # This is crucial to pair steps with resources from the config
        log_context.info("🔧 Pairing tasks with available resources...")
        finetuned_tasks = []
        for i, task in enumerate(self.tasks):
            if i < len(best_practices):
                finetuned_task = best_practice_manager.finetune_best_practice(
                    best_practices[i], task
                )
                # Update the task with the finetuned steps that include resource mappings
                task["steps"] = finetuned_task.get("steps", task.get("steps", []))
            finetuned_tasks.append(task)
        log_context.info(f"✅ Paired {len(finetuned_tasks)} tasks with resources")

        # Step 6: Refine best practices through human-in-the-loop if enabled
        if self.interactable_with_user and UI_AVAILABLE:
            log_context.info("👤 Starting human-in-the-loop refinement...")
            try:
                hitl_result = TaskEditorApp(finetuned_tasks).run()
                if hitl_result is not None:
                    # Apply additional refinement if human-in-the-loop is used
                    for idx_t, task in enumerate(hitl_result):
                        if idx_t < len(best_practices):
                            refined_task = best_practice_manager.finetune_best_practice(
                                best_practices[idx_t], task
                            )
                            finetuned_tasks[idx_t]["steps"] = refined_task.get(
                                "steps", task.get("steps", [])
                            )
                    log_context.info("✅ Human-in-the-loop refinement completed")
            except Exception as e:
                log_context.error(f"❌ Error in human-in-the-loop refinement: {str(e)}")

        # Step 7: Format the final task graph
        log_context.info("📊 Formatting final task graph...")
        task_graph_formatter = self._initialize_task_graph_formatter()

        # Format the final task graph with finetuned tasks (including resource mappings)
        task_graph = task_graph_formatter.format_task_graph(finetuned_tasks)

        # Add reusable tasks to the task graph output
        if self.reusable_tasks:
            task_graph["reusable_tasks"] = self.reusable_tasks
            log_context.info(
                f"📦 Added {len(self.reusable_tasks)} reusable tasks to graph"
            )

        log_context.info("🎉 Task graph generation completed successfully")
        return task_graph

    def save_task_graph(self, task_graph: Dict[str, Any]) -> str:
        """Save the task graph to a file.

        Args:
            task_graph (Dict[str, Any]): The task graph to save

        Returns:
            str: Path to the saved task graph file
        """
        import functools
        import collections.abc
        import json

        def sanitize(obj):
            if isinstance(obj, (str, int, float, bool)) or obj is None:
                return obj
            elif isinstance(obj, dict):
                return {k: sanitize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize(v) for v in obj]
            elif isinstance(obj, tuple):
                return tuple(sanitize(v) for v in obj)
            elif isinstance(obj, functools.partial):
                print(f"Found partial: {obj}")
                return str(obj)
            elif isinstance(obj, collections.abc.Callable):
                print(f"Found callable: {obj}")
                return str(obj)
            else:
                print(f"Found non-serializable: {obj} (type: {type(obj)})")
                return str(obj)

        # Debug print for non-serializable fields
        for k, v in task_graph.items():
            if not isinstance(v, (str, int, float, bool, list, dict, type(None))):
                print(f"Field {k} is non-serializable: {v} (type: {type(v)})")

        sanitized_task_graph = sanitize(task_graph)
        taskgraph_filepath = os.path.join(self.output_dir, f"taskgraph.json")
        with open(taskgraph_filepath, "w") as f:
            json.dump(sanitized_task_graph, f, indent=4)
        return taskgraph_filepath
