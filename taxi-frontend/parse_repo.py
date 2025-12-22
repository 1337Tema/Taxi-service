import os
import json

# --- Constants ---
STRUCTURE_ONLY_FILENAME = "folder_structure.txt"
STRUCTURE_WITH_CONTENT_FILENAME = "folder_structure_with_content.txt"
MAX_FILE_CONTENT_LINES = 10e10  # Max lines of content to include per file if requested
CSV_PREVIEW_LINES = 10          # Max lines of content to include for CSV files if requested

# List of common text file extensions (lowercase)
TEXT_FILE_EXTENSIONS = {
    # Plain Text & Markup
    '.txt', '.md', '.markdown', '.rst', '.tex', '.rtf', '.text', '.log',
    # Programming Languages
    '.py', '.pyw', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.js', '.mjs', '.cjs', '.ts', '.tsx',
    '.php', '.pl', '.pm', '.rb', '.swift', '.go', '.rs', '.lua', '.scala', '.kt', '.kts', '.dart',
    '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
    '.groovy', '.gvy', '.gy', '.gsh',
    '.r', '.jl', '.pas', '.f', '.f90', '.f95', '.for', # Fortran
    '.asm', '.s', # Assembly
    '.vb', '.vbs', # Visual Basic
    '.clj', '.cljs', '.cljc', '.edn', # Clojure
    '.erl', '.hrl', # Erlang
    '.ex', '.exs', # Elixir
    '.hs', '.lhs', # Haskell
    '.lisp', '.lsp', '.scm', # Lisp / Scheme
    '.ml', '.mli', # OCaml / ML
    '.pde', # Processing
    '.sol', # Solidity
    '.tcl',
    '.vala',
    # Web Development
    '.html', '.htm', '.xhtml', '.css', '.scss', '.less', '.sass', '.json', '.xml', '.svg',
    '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.properties',
    '.asp', '.aspx', '.jsp', '.ejs', '.hbs', '.mustache', '.pug', '.jade',
    '.htaccess', '.htpasswd',
    # Data Formats
    '.csv', '.tsv', '.jsonl', '.ndjson', '.sql', '.graphql', '.gql', # .csv остается здесь, но будет перехвачен раньше
    # Config & Build Files
    '.dockerfile', 'dockerfile',
    '.gitattributes', '.gitignore', '.gitmodules', '.editorconfig',
    'makefile', 'makefile.in', 'cmakelists.txt', 'meson.build',
    '.pom', '.gradle', '.sbt', '.project', '.classpath', '.build',
    '.csproj', '.vbproj', '.sln', '.suo',
    '.yaml-tml', # Helm charts
    # Documentation & Notes
    '.org', '.wiki', '.textile', '.adoc', '.asciidoc',
    # Subtitles
    '.srt', '.sub', '.vtt',
    # Others
    '.patch', '.diff', '.desktop', '.service', '.rules', # Linux specific
    '.reg', # Windows Registry
    '.plantuml', '.puml', '.pu', # PlantUML
    '.dot', '.gv', # Graphviz DOT
    # '.ipynb', # Убрано, обрабатывается отдельно
    '.pro', '.pri', '.src'
}
TEXT_FILE_EXTENSIONS.add('') # For files with no extension that might be text

# Encodings to try for reading text file content, in order of preference
ENCODINGS_TO_TRY_FOR_CONTENT = ['utf-8', 'cp1251', 'cp1252', 'latin-1', 'utf-16']


def _read_text_file_content_with_encodings(
    filepath,
    max_lines,
    base_prefix,
    output_file_obj
    ):
    """
    Tries to read a standard text file with a list of encodings and write its content.
    """
    for enc in ENCODINGS_TO_TRY_FOR_CONTENT:
        try:
            with open(filepath, 'r', encoding=enc, errors='strict') as f_content:
                output_file_obj.write(f"{base_prefix}--- File Content (text, encoding: {enc}, up to {max_lines} lines) ---\n")
                lines_written = 0
                content_found_and_printed = False
                for line_text in f_content:
                    if lines_written >= max_lines:
                        output_file_obj.write(f"{base_prefix}[...content truncated...]\n")
                        content_found_and_printed = True
                        break
                    output_file_obj.write(f"{base_prefix}{line_text.rstrip()}\n")
                    lines_written += 1
                    content_found_and_printed = True
                if not content_found_and_printed and lines_written == 0:
                     output_file_obj.write(f"{base_prefix}[File is empty or content not shown due to 0 line limit]\n")
                output_file_obj.write(f"{base_prefix}--- File Content End ---\n")
                return True
        except UnicodeDecodeError:
            continue
        except IOError as e:
            output_file_obj.write(f"{base_prefix}[IOError reading file (tried encoding {enc}): {e}]\n")
            return False
        except Exception as e:
            output_file_obj.write(f"{base_prefix}[Unexpected error reading file (tried encoding {enc}): {e}]\n")
            return False
    output_file_obj.write(f"{base_prefix}[Could not decode file using tried encodings ({', '.join(ENCODINGS_TO_TRY_FOR_CONTENT)}) - Content not displayed]\n")
    return False


def _read_ipynb_content(filepath, max_lines, base_prefix, output_file_obj):
    """
    Reads a .ipynb (Jupyter Notebook) file, extracts markdown and code cells.
    """
    output_file_obj.write(f"{base_prefix}--- Jupyter Notebook Content (markdown & code cells, up to {max_lines} lines total) ---\n")
    lines_written_total = 0
    content_processed = False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            notebook_data = json.load(f)
        
        if 'cells' not in notebook_data or not isinstance(notebook_data['cells'], list):
            output_file_obj.write(f"{base_prefix}[Invalid .ipynb format: 'cells' array not found]\n")
            output_file_obj.write(f"{base_prefix}--- Jupyter Notebook Content End ---\n")
            return False

        for i, cell in enumerate(notebook_data['cells']):
            if lines_written_total >= max_lines:
                break 
            cell_type = cell.get('cell_type')
            source = cell.get('source')
            if not isinstance(source, list):
                if isinstance(source, str): source = source.splitlines(keepends=True)
                else: continue

            if cell_type == 'markdown':
                if lines_written_total < max_lines:
                    header = f"{base_prefix}[Markdown Cell {i+1}]\n"
                    output_file_obj.write(header)
                    lines_written_total += header.count('\n')
                    content_processed = True
                for line in source:
                    if lines_written_total >= max_lines:
                        output_file_obj.write(f"{base_prefix}[...content truncated...]\n")
                        break
                    output_file_obj.write(f"{base_prefix}{line.rstrip()}\n")
                    lines_written_total += 1
            elif cell_type == 'code':
                if lines_written_total < max_lines:
                    header = f"{base_prefix}[Code Cell {i+1}]\n"
                    output_file_obj.write(header)
                    lines_written_total += header.count('\n')
                    content_processed = True
                for line in source:
                    if lines_written_total >= max_lines:
                        output_file_obj.write(f"{base_prefix}[...content truncated...]\n")
                        break
                    output_file_obj.write(f"{base_prefix}{line.rstrip()}\n")
                    lines_written_total += 1
        
        if not content_processed and lines_written_total == 0:
            output_file_obj.write(f"{base_prefix}[No markdown or code cells found, or content not shown due to 0 line limit]\n")

    except json.JSONDecodeError as e:
        output_file_obj.write(f"{base_prefix}[Error decoding .ipynb JSON: {e}]\n")
    except IOError as e:
        output_file_obj.write(f"{base_prefix}[IOError reading .ipynb file: {e}]\n")
    except Exception as e:
        output_file_obj.write(f"{base_prefix}[Unexpected error processing .ipynb file: {e}]\n")
    finally:
        output_file_obj.write(f"{base_prefix}--- Jupyter Notebook Content End ---\n")
    return content_processed

def _read_csv_content(filepath, max_preview_lines, base_prefix, output_file_obj):
    """
    Reads a .csv file and writes a preview (first N lines), trying multiple encodings.
    """
    content_successfully_read = False
    for enc in ENCODINGS_TO_TRY_FOR_CONTENT:
        try:
            with open(filepath, 'r', encoding=enc, errors='strict') as f_content:
                # Если открытие успешно, выводим информацию о кодировке и заголовок
                output_file_obj.write(f"{base_prefix}--- CSV File Content Preview (encoding: {enc}, up to {max_preview_lines} lines) ---\n")
                lines_written = 0
                content_found_in_this_attempt = False
                
                for line_text in f_content:
                    if lines_written >= max_preview_lines:
                        if lines_written > 0: # Только если что-то уже было написано
                             output_file_obj.write(f"{base_prefix}[...remaining content truncated...]\n")
                        content_found_in_this_attempt = True
                        break
                    output_file_obj.write(f"{base_prefix}{line_text.rstrip()}\n")
                    lines_written += 1
                    content_found_in_this_attempt = True
                
                if not content_found_in_this_attempt and lines_written == 0:
                     output_file_obj.write(f"{base_prefix}[File is empty or preview not shown due to 0 line limit]\n")
                
                output_file_obj.write(f"{base_prefix}--- CSV File Content Preview End ---\n")
                content_successfully_read = True
                return True # Успешно прочитали и записали с этой кодировкой
        
        except UnicodeDecodeError:
            continue # Пробуем следующую кодировку
        
        except IOError as e:
            output_file_obj.write(f"{base_prefix}--- CSV File Content Preview (attempted encoding: {enc}) ---\n")
            output_file_obj.write(f"{base_prefix}[IOError reading CSV file: {e}]\n")
            output_file_obj.write(f"{base_prefix}--- CSV File Content Preview End ---\n")
            return False # Прекращаем попытки для этого файла
        
        except Exception as e:
            output_file_obj.write(f"{base_prefix}--- CSV File Content Preview (attempted encoding: {enc}) ---\n")
            output_file_obj.write(f"{base_prefix}[Unexpected error processing CSV file: {e}]\n")
            output_file_obj.write(f"{base_prefix}--- CSV File Content Preview End ---\n")
            return False # Прекращаем попытки для этого файла

    # Если все кодировки не подошли
    if not content_successfully_read:
        output_file_obj.write(f"{base_prefix}--- CSV File Content Preview ---\n")
        output_file_obj.write(f"{base_prefix}[Could not decode CSV file using tried encodings ({', '.join(ENCODINGS_TO_TRY_FOR_CONTENT)}) - Preview not displayed]\n")
        output_file_obj.write(f"{base_prefix}--- CSV File Content Preview End ---\n")
    return False


def _write_folder_tree_recursive(
    current_folder_path,
    prefix="",
    output_file=None,
    output_filename_to_exclude=None,
    root_folder_abs_path=None,
    include_file_content=False,
    files_to_skip_content_processing=None
    ):
    if files_to_skip_content_processing is None:
        files_to_skip_content_processing = set()

    try:
        listed_entries = os.listdir(current_folder_path)
        listed_entries.sort()
    except PermissionError:
        if output_file: output_file.write(f"{prefix}├── [Access Denied]\n")
        return
    except FileNotFoundError:
        if output_file: output_file.write(f"{prefix}├── [Path not found - unexpected]\n")
        return

    entries_to_process = []
    current_folder_abs_path_for_check = os.path.abspath(current_folder_path)

    for entry_name in listed_entries:
        if (entry_name == output_filename_to_exclude and
                current_folder_abs_path_for_check == root_folder_abs_path):
            continue
        if entry_name.startswith('.'):
            continue
        entries_to_process.append(entry_name)

    pointers = ["├── "] * (len(entries_to_process) - 1) + ["└── "] if entries_to_process else []

    for i, entry_name in enumerate(entries_to_process):
        current_path = os.path.join(current_folder_path, entry_name)
        item_pointer = pointers[i]

        if os.path.isdir(current_path):
            output_file.write(f"{prefix}{item_pointer}{entry_name} (folder)\n")
            extension_for_next_level = "│   " if item_pointer == "├── " else "    "
            _write_folder_tree_recursive(
                current_path, prefix + extension_for_next_level, output_file,
                output_filename_to_exclude, root_folder_abs_path,
                include_file_content, files_to_skip_content_processing
            )
        elif os.path.isfile(current_path):
            output_file.write(f"{prefix}{item_pointer}{entry_name} (file)\n")
            if include_file_content:
                content_base_prefix_ext = "│   " if item_pointer == "├── " else "    "
                full_content_prefix = prefix + content_base_prefix_ext + "┆ "

                if entry_name in files_to_skip_content_processing:
                    output_file.write(f"{full_content_prefix}[Content of {entry_name} intentionally not processed for this report]\n")
                else:
                    _, file_ext = os.path.splitext(entry_name)
                    file_ext_lower = file_ext.lower()

                    if file_ext_lower == '.ipynb':
                        _read_ipynb_content(
                            current_path,
                            MAX_FILE_CONTENT_LINES, # Общее ограничение для ipynb
                            full_content_prefix,
                            output_file
                        )
                    elif file_ext_lower == '.csv': # <--- ОБРАБОТКА CSV
                        _read_csv_content(
                            current_path,
                            CSV_PREVIEW_LINES, # Специальное ограничение для CSV
                            full_content_prefix,
                            output_file
                        )
                    elif file_ext_lower in TEXT_FILE_EXTENSIONS:
                        _read_text_file_content_with_encodings(
                            current_path,
                            MAX_FILE_CONTENT_LINES, # Общее ограничение для остальных текстовых
                            full_content_prefix,
                            output_file
                        )
                    else:
                        output_file.write(f"{full_content_prefix}[Non-text file or unrecognized extension ('{file_ext}') - Content not displayed]\n")
        else:
            output_file.write(f"{prefix}{item_pointer}{entry_name} (other)\n")


def _generate_and_save_single_structure_file(
    root_folder_path,
    output_filename,
    include_file_content_flag,
    additional_files_to_skip_content=None
):
    if not os.path.exists(root_folder_path):
        print(f"Error: Path '{root_folder_path}' does not exist.")
        return False
    if not os.path.isdir(root_folder_path):
        print(f"Error: Path '{root_folder_path}' is not a directory.")
        return False

    output_filepath = os.path.join(root_folder_path, output_filename)
    root_folder_abs_path_for_check = os.path.abspath(root_folder_path)

    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(f"{os.path.basename(os.path.abspath(root_folder_path))} (folder)\n")
            _write_folder_tree_recursive(
                root_folder_path,
                prefix="  ",
                output_file=f,
                output_filename_to_exclude=output_filename,
                root_folder_abs_path=root_folder_abs_path_for_check,
                include_file_content=include_file_content_flag,
                files_to_skip_content_processing=additional_files_to_skip_content
            )
        print(f"Successfully saved to: {output_filepath}")
        return True
    except IOError as e:
        print(f"Error writing to file '{output_filepath}': {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while processing '{output_filename}': {e}")
        return False

if __name__ == "__main__":
    target_directory = input("Enter path to the folder to analyze (default: current directory): ")
    if not target_directory.strip():
        target_directory = "." 
        print(f"No path entered, using current directory: {os.path.abspath(target_directory)}")
    else:
        target_directory = target_directory.strip()

    parse_with_content_input = input(
        "Include text file content? (yes/no) [no]: "
    ).lower()
    should_parse_with_content = parse_with_content_input in ['yes', 'y']

    print(f"\nGenerating documentation for '{os.path.abspath(target_directory)}'...")

    print(f"\nAttempting to create structure-only file: '{STRUCTURE_ONLY_FILENAME}'")
    _generate_and_save_single_structure_file(
        target_directory,
        output_filename=STRUCTURE_ONLY_FILENAME,
        include_file_content_flag=False,
        additional_files_to_skip_content=None
    )

    if should_parse_with_content:
        print(f"\nAttempting to create structure-with-text-content file: '{STRUCTURE_WITH_CONTENT_FILENAME}'")
        files_to_skip_for_this_report = {STRUCTURE_ONLY_FILENAME}
        _generate_and_save_single_structure_file(
            target_directory,
            output_filename=STRUCTURE_WITH_CONTENT_FILENAME,
            include_file_content_flag=True,
            additional_files_to_skip_content=files_to_skip_for_this_report
        )

    print("\nDocumentation generation finished.")