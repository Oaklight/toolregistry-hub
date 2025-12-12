"""Unit tests for Utils module."""

from toolregistry_hub.utils.fn_namespace import (
    _is_all_static_methods,
    _determine_namespace,
    get_all_static_methods
)


class TestClass:
    """Test class with static methods for testing."""
    
    @staticmethod
    def static_method_one():
        """First static method."""
        pass
    
    @staticmethod
    def static_method_two():
        """Second static method."""
        pass
    
    def instance_method(self):
        """Instance method."""
        pass


class AllStaticClass:
    """Test class with only static methods."""
    
    @staticmethod
    def method_a():
        """Static method A."""
        pass
    
    @staticmethod
    def method_b():
        """Static method B."""
        pass


class NoStaticClass:
    """Test class with no static methods."""
    
    def method_one(self):
        """Instance method one."""
        pass
    
    def method_two(self):
        """Instance method two."""
        pass


class MixedClass:
    """Test class with mixed method types."""
    
    @staticmethod
    def static_method():
        """Static method."""
        pass
    
    @classmethod
    def class_method(cls):
        """Class method."""
        pass
    
    def instance_method(self):
        """Instance method."""
        pass
    
    @property
    def some_property(self):
        """Property."""
        return "value"


class TestIsAllStaticMethods:
    """Test cases for _is_all_static_methods function."""
    
    def test_all_static_methods(self):
        """Test class with only static methods."""
        assert _is_all_static_methods(AllStaticClass) is True
    
    def test_no_static_methods(self):
        """Test class with no static methods."""
        # The implementation checks if all methods are static, but NoStaticClass has regular methods
        assert _is_all_static_methods(NoStaticClass) is False  # Has non-static methods
    
    def test_mixed_methods(self):
        """Test class with mixed method types."""
        assert _is_all_static_methods(MixedClass) is False
    
    def test_test_class(self):
        """Test TestClass which has both static and instance methods."""
        assert _is_all_static_methods(TestClass) is False


class TestDetermineNamespace:
    """Test cases for _determine_namespace function."""
    
    def test_string_namespace(self):
        """Test with string namespace."""
        result = _determine_namespace(TestClass, "custom_namespace")
        assert result == "custom_namespace"
    
    def test_true_with_class(self):
        """Test with True and class."""
        result = _determine_namespace(TestClass, True)
        assert result == "TestClass"
    
    def test_true_with_instance(self):
        """Test with True and instance."""
        instance = TestClass()
        result = _determine_namespace(instance, True)
        assert result == "TestClass"
    
    def test_false_namespace(self):
        """Test with False namespace."""
        result = _determine_namespace(TestClass, False)
        assert result is None
    
    def test_empty_string_namespace(self):
        """Test with empty string namespace."""
        result = _determine_namespace(TestClass, "")
        assert result == ""


class TestGetAllStaticMethods:
    """Test cases for get_all_static_methods function."""
    
    def test_get_static_methods_from_class(self):
        """Test getting static methods from class."""
        methods = get_all_static_methods(TestClass)
        assert "static_method_one" in methods
        assert "static_method_two" in methods
        assert "instance_method" not in methods
        assert len(methods) == 2
    
    def test_get_static_methods_from_instance(self):
        """Test getting static methods from instance."""
        instance = TestClass()
        methods = get_all_static_methods(instance)
        assert "static_method_one" in methods
        assert "static_method_two" in methods
        assert "instance_method" not in methods
        assert len(methods) == 2
    
    def test_get_static_methods_with_skip_list(self):
        """Test getting static methods with skip list."""
        methods = get_all_static_methods(TestClass, skip_list=["static_method_two"])
        assert "static_method_one" in methods
        assert "static_method_two" not in methods
        assert len(methods) == 1
    
    def test_get_static_methods_with_include_list(self):
        """Test getting static methods with include list."""
        methods = get_all_static_methods(TestClass, include_list=["static_method_one"])
        assert "static_method_one" in methods
        assert "static_method_two" not in methods
        assert len(methods) == 1
    
    def test_get_static_methods_with_include_list_nonexistent(self):
        """Test getting static methods with include list containing non-existent method."""
        methods = get_all_static_methods(TestClass, include_list=["static_method_one", "nonexistent_method"])
        assert "static_method_one" in methods
        assert "nonexistent_method" not in methods
        assert len(methods) == 1
    
    def test_get_static_methods_empty_include_list(self):
        """Test getting static methods with empty include list."""
        methods = get_all_static_methods(TestClass, include_list=[])
        assert "static_method_one" in methods
        assert "static_method_two" in methods
        assert len(methods) == 2
    
    def test_get_static_methods_skip_and_include(self):
        """Test getting static methods with both skip and include lists."""
        methods = get_all_static_methods(
            TestClass, 
            skip_list=["static_method_one"], 
            include_list=["static_method_one", "static_method_two"]
        )
        # Include list is processed first, then skip list removes items
        assert "static_method_one" not in methods
        assert "static_method_two" in methods
        assert len(methods) == 1
    
    def test_get_static_methods_all_static_class(self):
        """Test getting static methods from class with only static methods."""
        methods = get_all_static_methods(AllStaticClass)
        assert "method_a" in methods
        assert "method_b" in methods
        assert len(methods) == 2
    
    def test_get_static_methods_no_static_class(self):
        """Test getting static methods from class with no static methods."""
        methods = get_all_static_methods(NoStaticClass)
        assert len(methods) == 0
    
    def test_get_static_methods_mixed_class(self):
        """Test getting static methods from class with mixed method types."""
        methods = get_all_static_methods(MixedClass)
        assert "static_method" in methods
        assert "class_method" not in methods
        assert "instance_method" not in methods
        assert "some_property" not in methods
        assert len(methods) == 1
    
    def test_get_static_methods_excludes_private(self):
        """Test that private methods are excluded."""
        class ClassWithPrivate:
            @staticmethod
            def public_method():
                pass
            
            @staticmethod
            def _private_method():
                pass
            
            @staticmethod
            def __dunder_method__():
                pass
        
        methods = get_all_static_methods(ClassWithPrivate)
        assert "public_method" in methods
        assert "_private_method" not in methods
        assert "__dunder_method__" not in methods
        assert len(methods) == 1
    
    def test_get_static_methods_none_skip_list(self):
        """Test getting static methods with None skip list."""
        methods = get_all_static_methods(TestClass, skip_list=None)
        assert "static_method_one" in methods
        assert "static_method_two" in methods
        assert len(methods) == 2
    
    def test_get_static_methods_none_include_list(self):
        """Test getting static methods with None include list."""
        methods = get_all_static_methods(TestClass, include_list=None)
        assert "static_method_one" in methods
        assert "static_method_two" in methods
        assert len(methods) == 2


class TestUtilsIntegration:
    """Integration tests for utils functions."""
    
    def test_workflow_example(self):
        """Test a typical workflow using the utils functions."""
        # Check if class has all static methods
        is_all_static = _is_all_static_methods(AllStaticClass)
        assert is_all_static is True
        
        # Determine namespace
        namespace = _determine_namespace(AllStaticClass, True)
        assert namespace == "AllStaticClass"
        
        # Get static methods
        methods = get_all_static_methods(AllStaticClass)
        assert len(methods) == 2
        assert "method_a" in methods
        assert "method_b" in methods
    
    def test_edge_case_empty_class(self):
        """Test with empty class."""
        class EmptyClass:
            pass
        
        assert _is_all_static_methods(EmptyClass) is True
        assert _determine_namespace(EmptyClass, True) == "EmptyClass"
        assert get_all_static_methods(EmptyClass) == []
    
    def test_class_with_only_properties(self):
        """Test class with only properties."""
        class PropertyClass:
            @property
            def prop1(self):
                return "value1"
            
            @property
            def prop2(self):
                return "value2"
        
        assert _is_all_static_methods(PropertyClass) is False
        methods = get_all_static_methods(PropertyClass)
        assert len(methods) == 0