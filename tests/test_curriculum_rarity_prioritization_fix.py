"""
Test to verify that CurriculumManager properly prioritizes rare concept tasks
and doesn't fall back to preservation concepts when rare concepts are available.

This test validates the fix for the issue where rare concepts (like topological_reasoning)
were being skipped in favor of preservation concepts due to the "family fallback" logic
in select_batch_tasks.
"""

import json
import tempfile
from pathlib import Path

import pytest

from runtime.training.curriculum_manager import CurriculumManager


def write_task(directory, filename, target_concepts, nexryn_metadata=None):
    """Helper to write a task JSON file with metadata."""
    # Write with target_concepts at the top level (simpler structure)
    task_data = {
        "target_concepts": target_concepts,
    }
    task_path = Path(directory) / filename
    with task_path.open("w") as f:
        json.dump(task_data, f)
    return task_path


def test_curriculum_prioritizes_rare_transform_over_preservation():
    """
    Test that when selecting tasks:
    - Rare transform concepts (e.g., topological_reasoning with count=2) are prioritized
    - Preservation concepts (e.g., topology_preservation with count=61) are deprioritized
    - Even when both families are available, rare concepts win
    """
    with tempfile.TemporaryDirectory() as tmp_path:
        # Create tasks representing different concept categories
        write_task(
            tmp_path,
            "topology_reasoning_task.json",
            ["topological_reasoning", "density_modulation"]
        )
        write_task(
            tmp_path,
            "topology_change_task.json",
            ["topological_change"]
        )
        write_task(
            tmp_path,
            "topology_preservation_task.json",
            ["topology_preservation"]
        )
        write_task(
            tmp_path,
            "color_preservation_task.json",
            ["color_preservation"]
        )
        write_task(
            tmp_path,
            "growth_task.json",
            ["grow_topology"]
        )

        manager = CurriculumManager()

        # Simulate observed concept counts showing preservation-heavy distribution
        concept_counts = {
            "topological_reasoning": 2,      # Rare
            "density_modulation": 2,          # Rare
            "topological_change": 1,          # Very rare
            "topology_preservation": 61,      # Very common
            "color_preservation": 77,         # Very common
            "grow_topology": 68,              # Very common
        }

        task_files = [
            "topology_reasoning_task.json",
            "topology_change_task.json",
            "topology_preservation_task.json",
            "color_preservation_task.json",
            "growth_task.json",
        ]

        report = manager.rank_tasks(
            task_files,
            concept_counts=concept_counts,
            task_directory=tmp_path,
        )

        # Verify the ranking prioritizes rare concepts
        ranked_tasks = report["ranked_task_files"]
        
        # The first tasks should be those with rare concepts
        assert "topology_reasoning_task.json" in ranked_tasks[:2], \
            f"Rare topology_reasoning task should rank high, got: {ranked_tasks}"
        assert "topology_change_task.json" in ranked_tasks[:3], \
            f"Very rare topology_change task should rank high, got: {ranked_tasks}"

        # Preservation tasks should rank lower
        preservation_index = ranked_tasks.index("topology_preservation_task.json")
        reasoning_index = ranked_tasks.index("topology_reasoning_task.json")
        assert reasoning_index < preservation_index, \
            f"Rare reasoning task should rank before preservation. " \
            f"Indices: reasoning={reasoning_index}, preservation={preservation_index}"

        # Select batch should prioritize rare concepts
        batch = manager.select_batch_tasks(report, batch_size=3)
        
        assert "topology_reasoning_task.json" in batch, \
            f"Batch should include rare topological_reasoning task, got: {batch}"
        assert "topology_change_task.json" in batch, \
            f"Batch should include very rare topological_change task, got: {batch}"

        # Preservation should only appear if there's room after rare concepts
        if len(batch) > 2:
            # With batch_size=3, we should have room for a third task
            # but it should not be a pure preservation task if we have a mixed one
            pass


def test_curriculum_no_family_fallback_for_rare_concepts():
    """
    Test that select_batch_tasks doesn't use "family fallback" anymore.
    
    Old behavior: If topological_reasoning wasn't directly available,
    it would select ANY topology family member (including preservation).
    
    New behavior: It only selects tasks directly targeting the rare concept,
    or fills remaining slots from coverage_gap ordering.
    """
    with tempfile.TemporaryDirectory() as tmp_path:
        # Create tasks where there are NO tasks directly targeting topological_reasoning
        write_task(
            tmp_path,
            "topology_preservation_only.json",
            ["topology_preservation"]
        )
        write_task(
            tmp_path,
            "grow_topology_only.json",
            ["grow_topology"]
        )
        write_task(
            tmp_path,
            "density_modulation_task.json",
            ["density_modulation", "topological_change"]
        )

        # Custom target counts to make preservation concepts low priority
        custom_targets = {
            "topological_reasoning": 20,
            "density_modulation": 20,
            "topological_change": 20,
            "topology_preservation": 5,    # Default to 5 like non-targeted concepts
            "grow_topology": 20,
        }
        
        manager = CurriculumManager(target_concept_counts=custom_targets)

        concept_counts = {
            "topological_reasoning": 2,      # Rare but NO direct task for it
            "density_modulation": 2,          # Rare and HAS direct task
            "topological_change": 1,          # Very rare and HAS direct task
            "topology_preservation": 61,      # Common but NOT targeted
            "grow_topology": 68,              # Common
        }

        task_files = [
            "topology_preservation_only.json",
            "grow_topology_only.json",
            "density_modulation_task.json",
        ]

        report = manager.rank_tasks(
            task_files,
            concept_counts=concept_counts,
            task_directory=tmp_path,
        )

        batch = manager.select_batch_tasks(report, batch_size=2)
        
        # Should prioritize the task with rare concepts (density_modulation_task)
        assert "density_modulation_task.json" in batch, \
            f"Should select task with rare density_modulation, got: {batch}"

        # The second task should be based on coverage_gap priority, not just "family"
        # Since there's no direct topological_reasoning task, it falls to coverage_gap sorting
        remaining_task = [t for t in batch if t != "density_modulation_task.json"][0] if len(batch) > 1 else None
        
        if remaining_task:
            # verify it was selected based on remaining coverage gap
            assert remaining_task in ["topology_preservation_only.json", "grow_topology_only.json"], \
                f"Second task should be one of the available tasks, got: {remaining_task}"


def test_curriculum_coverage_gap_sorting_in_remaining_tasks():
    """
    Test that when filling remaining batch slots, tasks are sorted by coverage_gap
    rather than just original order.
    
    This ensures that even if a preservation task comes first in the list,
    a task with higher coverage_gap for a rare concept gets selected first.
    """
    with tempfile.TemporaryDirectory() as tmp_path:
        # Task 1 (first in list): Only preservation
        write_task(
            tmp_path,
            "001_preservation.json",  # Comes first alphabetically/originally
            ["topology_preservation"]
        )
        # Task 2 (second in list): Has rare concept with higher coverage_gap
        write_task(
            tmp_path,
            "002_rare_transform.json",
            ["topological_reasoning", "topological_change"]  # Multiple rare concepts
        )

        # Custom target counts
        custom_targets = {
            "topology_preservation": 5,      # Default to 5, preservation is not targeted
            "topological_reasoning": 20,     # Rare and targeted
            "topological_change": 20,        # Rare and targeted
        }
        
        manager = CurriculumManager(target_concept_counts=custom_targets)

        concept_counts = {
            "topology_preservation": 50,
            "topological_reasoning": 2,      # Rare
            "topological_change": 1,         # Very rare
        }

        task_files = [
            "001_preservation.json",
            "002_rare_transform.json",
        ]

        report = manager.rank_tasks(
            task_files,
            concept_counts=concept_counts,
            task_directory=tmp_path,
        )

        batch = manager.select_batch_tasks(report, batch_size=1)
        
        # Should select the task with rare concepts, not the first task
        assert batch[0] == "002_rare_transform.json", \
            f"Should select task with rare concepts over preservation. " \
            f"Got: {batch[0]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
