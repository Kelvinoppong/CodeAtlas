"""
Code Parser - extracts symbols and references using Tree-sitter
"""

import re
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Try to import tree-sitter, fall back to regex-based parsing
try:
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


class SymbolKind(str, Enum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    IMPORT = "import"


@dataclass
class ExtractedSymbol:
    """A symbol extracted from source code"""
    name: str
    kind: SymbolKind
    start_line: int
    end_line: int
    start_col: int = 0
    end_col: int = 0
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parent_name: Optional[str] = None


@dataclass
class ExtractedImport:
    """An import statement extracted from source code"""
    module: str
    names: List[str] = field(default_factory=list)
    alias: Optional[str] = None
    line: int = 0
    is_relative: bool = False


@dataclass
class ParseResult:
    """Result of parsing a source file"""
    symbols: List[ExtractedSymbol] = field(default_factory=list)
    imports: List[ExtractedImport] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class CodeParser:
    """Parses source code to extract symbols and structure"""

    def __init__(self):
        self._parsers = {}
        self._setup_parsers()

    def _setup_parsers(self):
        """Set up tree-sitter parsers for supported languages"""
        if not TREE_SITTER_AVAILABLE:
            return

        try:
            # Python
            py_lang = Language(tree_sitter_python.language())
            py_parser = Parser(py_lang)
            self._parsers["python"] = py_parser

            # JavaScript
            js_lang = Language(tree_sitter_javascript.language())
            js_parser = Parser(js_lang)
            self._parsers["javascript"] = js_parser

            # TypeScript
            ts_lang = Language(tree_sitter_typescript.language_typescript())
            ts_parser = Parser(ts_lang)
            self._parsers["typescript"] = ts_parser
        except Exception as e:
            print(f"Warning: Could not initialize tree-sitter parsers: {e}")

    def parse(self, content: str, language: str) -> ParseResult:
        """Parse source code and extract symbols"""
        if language == "python":
            return self._parse_python(content)
        elif language in ("javascript", "typescript"):
            return self._parse_javascript(content, language)
        else:
            # Fallback: try regex-based extraction
            return self._parse_generic(content, language)

    def _parse_python(self, content: str) -> ParseResult:
        """Parse Python source code"""
        result = ParseResult()
        lines = content.split("\n")

        if TREE_SITTER_AVAILABLE and "python" in self._parsers:
            result = self._parse_python_treesitter(content)
        else:
            result = self._parse_python_regex(content, lines)

        return result

    def _parse_python_regex(self, content: str, lines: List[str]) -> ParseResult:
        """Fallback regex-based Python parsing"""
        result = ParseResult()
        current_class = None

        # Patterns
        class_pattern = re.compile(r"^class\s+(\w+)(?:\s*\([^)]*\))?\s*:")
        func_pattern = re.compile(r"^(\s*)def\s+(\w+)\s*\([^)]*\)\s*(?:->.*?)?\s*:")
        import_pattern = re.compile(r"^(?:from\s+([\w.]+)\s+)?import\s+(.+)$")
        docstring_pattern = re.compile(r'^\s*(?:"""|\'\'\')(.*)(?:"""|\'\'\')?', re.DOTALL)

        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue

            # Check for imports
            import_match = import_pattern.match(stripped)
            if import_match:
                from_module = import_match.group(1)
                imports_str = import_match.group(2)

                if from_module:
                    # from X import Y
                    names = [n.strip().split(" as ")[0] for n in imports_str.split(",")]
                    result.imports.append(ExtractedImport(
                        module=from_module,
                        names=names,
                        line=line_num,
                        is_relative=from_module.startswith("."),
                    ))
                else:
                    # import X
                    for mod in imports_str.split(","):
                        mod = mod.strip()
                        alias = None
                        if " as " in mod:
                            mod, alias = mod.split(" as ")
                            mod, alias = mod.strip(), alias.strip()
                        result.imports.append(ExtractedImport(
                            module=mod,
                            alias=alias,
                            line=line_num,
                        ))
                continue

            # Check for class definitions
            class_match = class_pattern.match(stripped)
            if class_match:
                class_name = class_match.group(1)
                current_class = class_name

                # Find end of class (next non-indented line or EOF)
                end_line = self._find_block_end(lines, i)

                # Get docstring
                docstring = self._extract_docstring(lines, i + 1)

                result.symbols.append(ExtractedSymbol(
                    name=class_name,
                    kind=SymbolKind.CLASS,
                    start_line=line_num,
                    end_line=end_line,
                    signature=f"class {class_name}",
                    docstring=docstring,
                ))
                continue

            # Check for function/method definitions
            func_match = func_pattern.match(line)
            if func_match:
                indent = func_match.group(1)
                func_name = func_match.group(2)

                # Find end of function
                end_line = self._find_block_end(lines, i)

                # Get docstring
                docstring = self._extract_docstring(lines, i + 1)

                # Determine if it's a method
                is_method = len(indent) > 0 and current_class is not None
                kind = SymbolKind.METHOD if is_method else SymbolKind.FUNCTION

                # Extract signature
                sig_match = re.search(r"def\s+\w+\s*(\([^)]*\))", line)
                signature = f"def {func_name}{sig_match.group(1)}" if sig_match else f"def {func_name}()"

                result.symbols.append(ExtractedSymbol(
                    name=func_name,
                    kind=kind,
                    start_line=line_num,
                    end_line=end_line,
                    signature=signature,
                    docstring=docstring,
                    parent_name=current_class if is_method else None,
                ))

        return result

    def _parse_python_treesitter(self, content: str) -> ParseResult:
        """Parse Python using tree-sitter"""
        result = ParseResult()
        parser = self._parsers["python"]
        tree = parser.parse(bytes(content, "utf8"))

        def extract_text(node) -> str:
            return content[node.start_byte:node.end_byte]

        def visit(node, parent_class=None):
            if node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = extract_text(name_node)
                    docstring = self._get_docstring_from_node(node, content)
                    result.symbols.append(ExtractedSymbol(
                        name=name,
                        kind=SymbolKind.CLASS,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        signature=f"class {name}",
                        docstring=docstring,
                    ))
                    # Visit children with this class as parent
                    for child in node.children:
                        visit(child, parent_class=name)
                    return

            elif node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = extract_text(name_node)
                    params_node = node.child_by_field_name("parameters")
                    params = extract_text(params_node) if params_node else "()"
                    docstring = self._get_docstring_from_node(node, content)

                    kind = SymbolKind.METHOD if parent_class else SymbolKind.FUNCTION

                    result.symbols.append(ExtractedSymbol(
                        name=name,
                        kind=kind,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        signature=f"def {name}{params}",
                        docstring=docstring,
                        parent_name=parent_class,
                    ))

            elif node.type == "import_statement":
                # import X
                for child in node.children:
                    if child.type == "dotted_name":
                        result.imports.append(ExtractedImport(
                            module=extract_text(child),
                            line=node.start_point[0] + 1,
                        ))

            elif node.type == "import_from_statement":
                # from X import Y
                module = ""
                names = []
                for child in node.children:
                    if child.type == "dotted_name":
                        module = extract_text(child)
                    elif child.type == "import_prefix":
                        module = extract_text(child)
                    elif child.type in ("identifier", "dotted_name"):
                        if module:
                            names.append(extract_text(child))

                if module:
                    result.imports.append(ExtractedImport(
                        module=module,
                        names=names,
                        line=node.start_point[0] + 1,
                        is_relative=module.startswith("."),
                    ))

            # Recurse into children
            for child in node.children:
                visit(child, parent_class)

        visit(tree.root_node)
        return result

    def _get_docstring_from_node(self, node, content: str) -> Optional[str]:
        """Extract docstring from a function/class node"""
        # Look for first expression_statement child with string
        body = node.child_by_field_name("body")
        if body and body.children:
            first_stmt = body.children[0]
            if first_stmt.type == "expression_statement":
                for child in first_stmt.children:
                    if child.type == "string":
                        docstring = content[child.start_byte:child.end_byte]
                        # Clean up quotes
                        docstring = docstring.strip("'\"")
                        if docstring.startswith('""'):
                            docstring = docstring[2:]
                        if docstring.endswith('""'):
                            docstring = docstring[:-2]
                        return docstring.strip()
        return None

    def _parse_javascript(self, content: str, language: str) -> ParseResult:
        """Parse JavaScript/TypeScript source code"""
        result = ParseResult()

        if TREE_SITTER_AVAILABLE and language in self._parsers:
            result = self._parse_js_treesitter(content, language)
        else:
            result = self._parse_js_regex(content)

        return result

    def _parse_js_regex(self, content: str) -> ParseResult:
        """Fallback regex-based JS parsing"""
        result = ParseResult()
        lines = content.split("\n")

        # Patterns
        func_pattern = re.compile(
            r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)"
        )
        arrow_pattern = re.compile(
            r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>"
        )
        class_pattern = re.compile(r"(?:export\s+)?class\s+(\w+)")
        import_pattern = re.compile(
            r"import\s+(?:{([^}]+)}|(\w+))\s+from\s+['\"]([^'\"]+)['\"]"
        )

        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()

            # Check imports
            import_match = import_pattern.search(stripped)
            if import_match:
                named = import_match.group(1)
                default = import_match.group(2)
                module = import_match.group(3)

                names = []
                if named:
                    names = [n.strip().split(" as ")[0] for n in named.split(",")]
                if default:
                    names = [default]

                result.imports.append(ExtractedImport(
                    module=module,
                    names=names,
                    line=line_num,
                    is_relative=module.startswith("."),
                ))
                continue

            # Check classes
            class_match = class_pattern.search(stripped)
            if class_match:
                result.symbols.append(ExtractedSymbol(
                    name=class_match.group(1),
                    kind=SymbolKind.CLASS,
                    start_line=line_num,
                    end_line=line_num,  # Simplified
                    signature=f"class {class_match.group(1)}",
                ))
                continue

            # Check functions
            func_match = func_pattern.search(stripped)
            if func_match:
                result.symbols.append(ExtractedSymbol(
                    name=func_match.group(1),
                    kind=SymbolKind.FUNCTION,
                    start_line=line_num,
                    end_line=line_num,  # Simplified
                    signature=stripped.split("{")[0].strip(),
                ))
                continue

            # Check arrow functions
            arrow_match = arrow_pattern.search(stripped)
            if arrow_match:
                result.symbols.append(ExtractedSymbol(
                    name=arrow_match.group(1),
                    kind=SymbolKind.FUNCTION,
                    start_line=line_num,
                    end_line=line_num,
                    signature=f"const {arrow_match.group(1)} = () =>",
                ))

        return result

    def _parse_js_treesitter(self, content: str, language: str) -> ParseResult:
        """Parse JS/TS using tree-sitter"""
        result = ParseResult()
        parser = self._parsers[language]
        tree = parser.parse(bytes(content, "utf8"))

        def extract_text(node) -> str:
            return content[node.start_byte:node.end_byte]

        def visit(node, parent_class=None):
            if node.type in ("class_declaration", "class"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = extract_text(name_node)
                    result.symbols.append(ExtractedSymbol(
                        name=name,
                        kind=SymbolKind.CLASS,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        signature=f"class {name}",
                    ))
                    for child in node.children:
                        visit(child, parent_class=name)
                    return

            elif node.type in ("function_declaration", "function"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = extract_text(name_node)
                    result.symbols.append(ExtractedSymbol(
                        name=name,
                        kind=SymbolKind.FUNCTION,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        signature=f"function {name}()",
                    ))

            elif node.type == "method_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = extract_text(name_node)
                    result.symbols.append(ExtractedSymbol(
                        name=name,
                        kind=SymbolKind.METHOD,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        signature=f"{name}()",
                        parent_name=parent_class,
                    ))

            elif node.type == "import_statement":
                source_node = node.child_by_field_name("source")
                if source_node:
                    module = extract_text(source_node).strip("'\"")
                    names = []

                    for child in node.children:
                        if child.type == "import_clause":
                            for sub in child.children:
                                if sub.type == "identifier":
                                    names.append(extract_text(sub))
                                elif sub.type == "named_imports":
                                    for spec in sub.children:
                                        if spec.type == "import_specifier":
                                            name_node = spec.child_by_field_name("name")
                                            if name_node:
                                                names.append(extract_text(name_node))

                    result.imports.append(ExtractedImport(
                        module=module,
                        names=names,
                        line=node.start_point[0] + 1,
                        is_relative=module.startswith("."),
                    ))

            for child in node.children:
                visit(child, parent_class)

        visit(tree.root_node)
        return result

    def _parse_generic(self, content: str, language: str) -> ParseResult:
        """Generic fallback parser for unsupported languages"""
        # Just return empty result for now
        return ParseResult()

    def _find_block_end(self, lines: List[str], start_idx: int) -> int:
        """Find the end of a Python block (class/function)"""
        if start_idx >= len(lines):
            return start_idx + 1

        # Get the indentation of the definition line
        def_line = lines[start_idx]
        def_indent = len(def_line) - len(def_line.lstrip())

        # Find next line with same or less indentation
        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            if not line.strip():  # Skip empty lines
                continue
            if line.strip().startswith("#"):  # Skip comments
                continue

            current_indent = len(line) - len(line.lstrip())
            if current_indent <= def_indent:
                return i

        return len(lines)

    def _extract_docstring(self, lines: List[str], start_idx: int) -> Optional[str]:
        """Extract docstring from lines after a definition"""
        if start_idx >= len(lines):
            return None

        # Look for triple-quoted string
        for i in range(start_idx, min(start_idx + 3, len(lines))):
            line = lines[i].strip()
            if line.startswith('"""') or line.startswith("'''"):
                quote = line[:3]
                if line.endswith(quote) and len(line) > 6:
                    return line[3:-3].strip()
                # Multi-line docstring
                docstring_lines = [line[3:]]
                for j in range(i + 1, len(lines)):
                    doc_line = lines[j]
                    if quote in doc_line:
                        docstring_lines.append(doc_line.split(quote)[0])
                        break
                    docstring_lines.append(doc_line)
                return "\n".join(docstring_lines).strip()
            elif not line:
                continue
            else:
                break

        return None
