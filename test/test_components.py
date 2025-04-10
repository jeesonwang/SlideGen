import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "slidegen"))

from pptx import Presentation

from slidegen.core.pptgen.components import components_manager


def test_components_manager():
    print(f"Available layout types: {components_manager.layout_types_names}")
    layout = components_manager.get_layout_type("two_points")
    if layout:
        print(f"Available styles for two_points: {layout.style_names}")
        print(f"Available styles for two_points: {layout.style_list}")
    assert "two_points" in components_manager.layout_types_names
    random_style = components_manager.get_random_style("two_points")
    if random_style:
        print(f"Randomly selected style: {random_style.name}")

        for shape_name, shape in random_style.shapes.items():
            print(f"  Shape: {shape_name}, Content type: {shape.content_type}")


def test_add_style():
    path = "data/深度学习原理架构与应用.pptx"
    presentation = Presentation(path)
    slide = presentation.slides[16]
    components_manager.add_style_from_slide(slide, "one_point", "style1")
    components_manager.save_to_json("components/shapes/shapes.json")
    components_manager.reload("components/shapes/shapes.json")

    layout = components_manager.get_layout_type("one_points")
    assert "style1" in layout.style_names
    print(f"Available styles for one_points: {layout.style_names}")
    print(f"Available styles for one_points: {layout.style_list}")
