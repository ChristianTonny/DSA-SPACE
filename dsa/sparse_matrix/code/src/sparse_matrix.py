import os

# Implements a sparse matrix using dictionary-based storage for non-zero elements
class SparseMatrix:
    def __init__(self, source, num_cols=None):
        # Initialize empty matrix data and dimensions
        self.matrix_data = {}
        self.file_declared_max_row = -1 
        self.file_declared_max_col = -1
        self.rows = 0
        self.cols = 0

        # Handle initialization from file path or dimensions
        if isinstance(source, str):
            self._parse_file(source)
        elif isinstance(source, int) and isinstance(num_cols, int):
            num_rows_count = source
            num_cols_count = num_cols
            if num_rows_count < 0 or num_cols_count < 0:
                raise ValueError("Matrix dimension counts must be non-negative.")
            
            self.rows = num_rows_count
            self.cols = num_cols_count
            self.file_declared_max_row = num_rows_count - 1
            self.file_declared_max_col = num_cols_count - 1
        else:
            raise TypeError("Invalid arguments for SparseMatrix constructor.")

    # Helper to validate integer strings
    def _is_valid_int(self, s_val):
        s_val = s_val.strip()
        if not s_val: return False
        if s_val[0] in "+-": return len(s_val) > 1 and s_val[1:].isdigit()
        return s_val.isdigit()

    # Parse matrix data from input file
    def _parse_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file not found: {file_path}")

        parsed_rows = parsed_cols = False
        self.file_declared_max_row = self.file_declared_max_col = -2

        # Process each line in the file
        for line_num, raw_line in enumerate(lines):
            line = raw_line.strip()
            if not line: continue

            # Parse rows definition
            if line.startswith("rows="):
                if parsed_rows:
                    raise ValueError("Input file has wrong format: 'rows' specified multiple times.")
                try:
                    val_str = line.split('=')[1].strip()
                    self._validate_and_set_dimension(val_str, line_num, raw_line, "row")
                    parsed_rows = True
                except (IndexError, ValueError) as e:
                    if "Input file has wrong format" in str(e): raise
                    raise ValueError(f"Input file has wrong format: Malformed 'rows' entry on line {line_num + 1}")
            
            # Parse cols definition
            elif line.startswith("cols="):
                if parsed_cols:
                    raise ValueError("Input file has wrong format: 'cols' specified multiple times.")
                try:
                    val_str = line.split('=')[1].strip()
                    self._validate_and_set_dimension(val_str, line_num, raw_line, "col")
                    parsed_cols = True
                except (IndexError, ValueError) as e:
                    if "Input file has wrong format" in str(e): raise
                    raise ValueError(f"Input file has wrong format: Malformed 'cols' entry on line {line_num + 1}")

            # Parse matrix entries
            elif line.startswith("(") and line.endswith(")"):
                if not parsed_rows or not parsed_cols:
                    raise ValueError("Input file has wrong format: Matrix dimensions must be defined before data entries.")
                
                parts = [p.strip() for p in line[1:-1].strip().split(',')]

                if len(parts) != 3 or not all(self._is_valid_int(p) for p in parts):
                    raise ValueError(f"Input file has wrong format: Invalid data entry on line {line_num + 1}")

                r, c, v = map(int, parts)

                if not (0 <= r < self.rows and 0 <= c < self.cols):
                    raise ValueError(f"Input file has wrong format: Data entry ({r},{c}) out of bounds.")
                
                self.set_element(r, c, v)
            else:
                raise ValueError(f"Input file has wrong format: Unrecognized line format on line {line_num + 1}")

        if not parsed_rows or not parsed_cols:
            raise ValueError("Input file has wrong format: Missing 'rows' or 'cols' definition.")
            
    # Validate and set matrix dimensions
    def _validate_and_set_dimension(self, val_str, line_num, raw_line, dim_type):
        if not self._is_valid_int(val_str):
            raise ValueError(f"Input file has wrong format: '{dim_type}s' value is not an integer")
        
        declared_max = int(val_str)
        if declared_max < -1:
            raise ValueError(f"Input file has wrong format: '{dim_type}s' value cannot be less than -1")
        
        if dim_type == "row":
            self.file_declared_max_row = declared_max
            self.rows = declared_max + 1
        else:
            self.file_declared_max_col = declared_max
            self.cols = declared_max + 1

    # Get element at specified position
    def get_element(self, curr_row, curr_col):
        if not (0 <= curr_row < self.rows and 0 <= curr_col < self.cols):
            raise IndexError("Element index out of bounds.")
        return self.matrix_data.get(curr_row, {}).get(curr_col, 0)

    # Set element at specified position
    def set_element(self, curr_row, curr_col, value):
        if not (0 <= curr_row < self.rows and 0 <= curr_col < self.cols):
            raise IndexError("Element index out of bounds.")
        
        if not isinstance(value, int):
            raise ValueError("Value must be an integer.")

        if value == 0:
            if curr_row in self.matrix_data and curr_col in self.matrix_data[curr_row]:
                del self.matrix_data[curr_row][curr_col]
                if not self.matrix_data[curr_row]:
                    del self.matrix_data[curr_row]
        else:
            self.matrix_data.setdefault(curr_row, {})[curr_col] = value

    # String representation of matrix
    def __str__(self):
        s = f"Rows: {self.rows}, Cols: {self.cols}\nNon-zero elements:\n"
        if not self.matrix_data:
            s += "  (No non-zero elements)\n"
        else:
            for r in sorted(self.matrix_data.keys()):
                for c in sorted(self.matrix_data[r].keys()):
                    s += f"  ({r}, {c}, {self.matrix_data[r][c]})\n"
        return s

    # Generic operation between two matrices
    def operate(self, other_matrix, operation):
        if not isinstance(other_matrix, SparseMatrix):
            raise TypeError("Operand must be a SparseMatrix instance.")
        if self.rows != other_matrix.rows or self.cols != other_matrix.cols:
            raise ValueError("Matrices must have the same dimensions for this operation.")

        result_matrix = SparseMatrix(self.rows, self.cols)

        for r, cols_data in self.matrix_data.items():
            for c, val in cols_data.items():
                result_matrix.set_element(r, c, val)

        for r, cols_data in other_matrix.matrix_data.items():
            for c, val in cols_data.items():
                current_val = result_matrix.get_element(r, c)
                result_matrix.set_element(r, c, operation(current_val, val))
        
        return result_matrix
        
    # Matrix addition
    def add(self, other_matrix):
        return self.operate(other_matrix, lambda x, y: x + y)

    # Matrix subtraction
    def subtract(self, other_matrix):
        return self.operate(other_matrix, lambda x, y: x - y)

    # Matrix multiplication
    def multiply(self, other_matrix):
        if not isinstance(other_matrix, SparseMatrix):
            raise TypeError("Operand must be a SparseMatrix instance.")
        if self.cols != other_matrix.rows:
            raise ValueError("Incompatible dimensions for matrix multiplication.")

        result_matrix = SparseMatrix(self.rows, other_matrix.cols)
        
        for r1, row_data1 in self.matrix_data.items():
            for c1, val1 in row_data1.items():
                if c1 in other_matrix.matrix_data:
                    for c2, val2 in other_matrix.matrix_data[c1].items():
                        current_val = result_matrix.get_element(r1, c2)
                        result_matrix.set_element(r1, c2, current_val + val1 * val2)
        return result_matrix
        
    # Save matrix to file
    def save_to_file(self, file_path):
        with open(file_path, 'w') as f:
            f.write(f"rows={self.rows - 1}\n")
            f.write(f"cols={self.cols - 1}\n")
            for r in sorted(self.matrix_data.keys()):
                for c in sorted(self.matrix_data[r].keys()):
                    value = self.matrix_data[r][c]
                    if value != 0:
                        f.write(f"({r}, {c}, {value})\n")

# Get non-empty input from user
def get_user_input(prompt):
    while True:
        user_input = input(prompt).strip()
        if user_input:
            return user_input
        print("Input cannot be empty. Please try again.")

# Convert relative path to absolute path
def get_file_path(user_path, base_dir):
    return user_path if os.path.isabs(user_path) else os.path.join(base_dir, user_path)

# Execute requested matrix operation
def perform_operation(matrix1, matrix2, choice):
    operations = {
        '1': ('Addition', matrix1.add),
        '2': ('Subtraction', matrix1.subtract),
        '3': ('Multiplication', matrix1.multiply)
    }
    operation_name, operation_func = operations[choice]
    print(f"\nPerforming {operation_name}...")
    return operation_name, operation_func(matrix2)

# Main program execution
if __name__ == "__main__":
    print("Sparse Matrix Operations\n------------------------")

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()

    sample_inputs_base_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "sample_inputs"))
    output_base_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))

    while True:
        print("\nSelect an operation:")
        print("1. Addition (+)")
        print("2. Subtraction (-)")
        print("3. Multiplication (*)")
        print("4. Exit")
        
        choice = get_user_input("Enter your choice (1-4): ")

        if choice == '4':
            print("Exiting program.")
            break
        
        if choice not in ['1', '2', '3']:
            print("Invalid choice. Please enter a number between 1 and 3, or 4 to exit.")
            continue

        try:
            user_path1 = get_user_input("Enter the file path for the first matrix: ")
            actual_path1 = get_file_path(user_path1, sample_inputs_base_dir)
            
            print(f"Attempting to load matrix 1 from: {actual_path1}")
            matrix1 = SparseMatrix(actual_path1)
            print(f"Successfully loaded matrix 1.")

            user_path2 = get_user_input("Enter the file path for the second matrix: ")
            actual_path2 = get_file_path(user_path2, sample_inputs_base_dir)

            print(f"Attempting to load matrix 2 from: {actual_path2}")
            matrix2 = SparseMatrix(actual_path2)
            print(f"Successfully loaded matrix 2.")

            operation_name, result_matrix = perform_operation(matrix1, matrix2, choice)
            
            output_filename = "result.txt"
            output_path = os.path.join(output_base_dir, output_filename)
            result_matrix.save_to_file(output_path)
            print(f"{operation_name} successful. Result saved to {output_path}")

        except FileNotFoundError as e:
            print(f"Error: {e}. Please check the file path and ensure the file exists.")
        except (ValueError, TypeError, IndexError) as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
