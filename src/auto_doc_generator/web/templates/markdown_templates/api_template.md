# API Documentation

*Generated on {{ generation_date }}*

This document provides detailed API reference for all classes, functions, and modules in the codebase.

## Classes

{% for class in classes %}
### `{{ class.name }}`

**File**: [`{{ class.file }}`]({{ class.file }})  
**Line**: {{ class.line_number }}

{% if class.docstring %}
{{ class.docstring }}
{% else %}
*No documentation provided.*
{% endif %}

{% if class.bases and class.bases != ['object'] %}
**Inheritance**: 
```python
{{ class.bases | join(' -> ') }} -> {{ class.name }}
```
{% endif %}

{% if class.methods %}
**Methods**:

{% for method in class.methods %}
- `{{ method }}()`
{% endfor %}
{% endif %}

{% if class.decorators %}
**Decorators**: {{ class.decorators | join(', ') }}
{% endif %}

**Usage Example**:
```python
# Example usage of {{ class.name }}
instance = {{ class.name }}()
# Call methods as needed
```

---

{% endfor %}

## Functions

{% for func in functions %}
### `{{ func.name }}()`

**File**: [`{{ func.file }}`]({{ func.file }})  
**Line**: {{ func.line_number }}

{% if func.docstring %}
{{ func.docstring }}
{% else %}
*No documentation provided.*
{% endif %}

**Signature**:
```python
{% if func.is_async %}async {% endif %}def {{ func.name }}({% if func.args %}{{ func.args | join(', ') }}{% endif %}){% if func.returns_type %} -> {{ func.returns_type }}{% endif %}:
    pass
```

{% if func.args %}
**Parameters**:
{% for arg in func.args %}
- `{{ arg }}`: Parameter (type not specified)
{% endfor %}
{% endif %}

{% if func.returns_type %}
**Returns**: `{{ func.returns_type }}`
{% endif %}

{% if func.decorators %}
**Decorators**: {{ func.decorators | join(', ') }}
{% endif %}

**Usage Example**:
```python
{% if func.is_async %}
# Async function usage
result = await {{ func.name }}({% if func.args %}{{ func.args[:2] | join(', ') }}{% endif %})
{% else %}
# Function usage  
result = {{ func.name }}({% if func.args %}{{ func.args[:2] | join(', ') }}{% endif %})
{% endif %}
```

---

{% endfor %}

## Modules

{% for module in modules %}
### `{{ module.name }}`

**Path**: [`{{ module.path }}`]({{ module.path }})  
**Lines of Code**: {{ module.lines_of_code }}

{% if module.docstring %}
{{ module.docstring }}
{% else %}
*No module documentation provided.*
{% endif %}

**Contains**:
- {{ module.classes | length }} class{% if module.classes | length != 1 %}es{% endif %}
- {{ module.functions | length }} function{% if module.functions | length != 1 %}s{% endif %}

{% if module.classes %}
**Classes**: {{ module.classes | join(', ') }}
{% endif %}

{% if module.functions %}
**Functions**: {{ module.functions | join(', ') }}
{% endif %}

{% if module.imports %}
**Dependencies**:
{% for import in module.imports[:10] %}
- `{{ import }}`
{% endfor %}
{% if module.imports | length > 10 %}
- *... and {{ module.imports | length - 10 }} more*
{% endif %}
{% endif %}

**Import Statement**:
```python
import {{ module.name }}
# or
from {{ module.name }} import ClassName, function_name
```

---

{% endfor %}

## Quick Reference

### Class Hierarchy

```mermaid
classDiagram
{% for class in classes[:10] %}
  class {{ class.name }} {
    {% for method in class.methods[:5] %}
    {{ method }}()
    {% endfor %}
  }
  {% for base in class.bases %}
  {% if base != 'object' %}
  {{ base }} <|-- {{ class.name }}
  {% endif %}
  {% endfor %}
{% endfor %}
```

### Function Categories

{% set func_categories = {} %}
{% for func in functions %}
  {% set category = 'General' %}
  {% if 'init' in func.name or 'setup' in func.name %}
    {% set category = 'Initialization' %}
  {% elif 'process' in func.name or 'transform' in func.name %}
    {% set category = 'Data Processing' %}
  {% elif 'get' in func.name or 'fetch' in func.name %}
    {% set category = 'Data Retrieval' %}
  {% elif 'save' in func.name or 'write' in func.name %}
    {% set category = 'Data Storage' %}
  {% endif %}
  {% if func_categories.update({category: func_categories.get(category, []) + [func.name]}) %}{% endif %}
{% endfor %}

{% for category, funcs in func_categories.items() %}
#### {{ category }}
{% for func_name in funcs[:10] %}
- `{{ func_name }}()`
{% endfor %}
{% if funcs | length > 10 %}
- *... and {{ funcs | length - 10 }} more*
{% endif %}

{% endfor %}

## API Usage Guidelines

### Best Practices

1. **Error Handling**: Always wrap API calls in try-except blocks
2. **Type Hints**: Use type hints when calling functions for better IDE support
3. **Documentation**: Refer to function docstrings for detailed parameter information
4. **Testing**: Write unit tests for functions you use extensively

### Common Patterns

```python
# Pattern 1: Class instantiation and method calls
instance = ClassName()
result = instance.method_name(parameters)

# Pattern 2: Direct function calls
from module_name import function_name
result = function_name(parameters)

# Pattern 3: Error handling
try:
    result = risky_function()
except SpecificError as e:
    handle_error(e)
```

---

*This API documentation was automatically generated from code analysis. For the most up-to-date information, refer to the source code and inline documentation.*
