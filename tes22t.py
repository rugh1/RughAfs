import os

def generate_python_file_docs(folder_path, output_filename="README.md"):
    """
    Scans a specified folder for .py files and adds their filenames
    as titles and their content to an output file.

    Args:
        folder_path (str): The path to the folder to scan.
        output_filename (str): The name of the file where the documentation will be saved.
                               Defaults to "README.md".
    """
    python_files = []
    
    # Check if the folder exists
    if not os.path.isdir(folder_path):
        print(f"Error: Folder '{folder_path}' not found.")
        return

    # Walk through the directory and its subdirectories to find .py files
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                # Get the full path to the file
                full_file_path = os.path.join(root, file)
                # Get the relative path for the display in the README
                relative_path = os.path.relpath(full_file_path, folder_path)
                python_files.append((relative_path, full_file_path)) # Store both for later

    # Sort the files alphabetically by their relative path
    python_files.sort(key=lambda x: x[0])

    # Create the content for the output file
    output_content = f"# Documentation for Python Files in '{os.path.basename(folder_path)}'\n\n"
    if python_files:
        output_content += "This document contains the content of all Python (.py) files found in this directory and its subdirectories.\n\n"
        
        for relative_path, full_file_path in python_files:
            output_content += f"## {relative_path}\n\n" # Markdown heading for the filename
            output_content += "python\n" # Start a Markdown code block
            
            try:
                with open(full_file_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                    output_content += file_content
            except UnicodeDecodeError:
                output_content += f"Error: Could not read file '{relative_path}' with UTF-8 encoding. It might contain non-UTF-8 characters.\n"
            except IOError as e:
                output_content += f"Error reading file '{relative_path}': {e}\n"
            
            output_content += "\n\n" # End the Markdown code block
    else:
        output_content += "No Python files (.py) were found in this directory or its subdirectories.\n"

    # Write the content to the output file
    try:
        output_file_path = os.path.join(folder_path, output_filename)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(output_content)
        print(f"Successfully generated '{output_filename}' in '{folder_path}'.")
    except IOError as e:
        print(f"Error writing to file '{output_filename}': {e}")

if __name__ == "__main__":
    # --- Configuration ---
    # IMPORTANT: Replace 'path/to/your/folder' with the actual path to the folder you want to scan.
    # For example, if the script is in the same folder as your Python files, you can use '.'
    # current_directory = "." 
    
    # Or specify an absolute path:
    # my_target_folder = r"C:\Users\YourUser\Documents\MyProject" 
    
    # Or a relative path from where you run the script:
    my_target_folder = "kerberos" # Example: a subfolder named 'my_python_project'

    # --- Run the script ---
    generate_python_file_docs(my_target_folder, "README.md")
    # You can change "README.md" to "code_documentation.md" or any other desired name.