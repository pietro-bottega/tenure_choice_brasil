import os
import pandas as pd

data_folder = "../data"

def load_pnad_dictionary(file):
    """
    Reads the Excel variable dictionary and returns a cleaned pandas DataFrame.
    
    Parameters:
    file_path (str): The path to the .xls dictionary file.
    
    Returns:
    pd.DataFrame: A DataFrame with 'start', 'size', and 'var' columns.
    """
    # 0. Define path
    file_path = os.path.join(data_folder, file)
    
    # 1. Read the excel file, skipping the first row as specified
    df = pd.read_excel(file_path, skiprows=1)
    
    # 2. Keep only the first three columns (index 0, 1, and 2)
    df = df.iloc[:, :3]
    
    # 3. Rename the columns for easier reference later in the analysis
    df.columns = ['start', 'size', 'var']
    
    # 4. Drop any rows where the 'size' column is empty (NaN)
    df.dropna(subset=['size'], inplace=True)
    
    # 5. Return the cleaned DataFrame
    return df

def load_pnad_data(df_dict, file, col_name_var='var', col_name_size='size'):
    """
    Reads a fixed-width text file into a Pandas DataFrame using an existing dictionary.
    
    Parameters:
    df_dict (pd.DataFrame): The dictionary DataFrame containing column names and sizes.
    data_file_path (str): The path to the text/csv data file.
    col_name_var (str): The name of the column in df_dict that holds variable names.
    col_name_size (str): The name of the column in df_dict that holds variable sizes.
    
    Returns:
    pd.DataFrame: The structured dataset.
    """
    # 0. Define path
    file_path = os.path.join(data_folder, file)
    
    # 1. Extract the variable names into a list
    variables = df_dict[col_name_var].dropna().tolist()
    
    # 2. Extract the sizes into a list of integers
    sizes = df_dict[col_name_size].dropna().astype(int).tolist()
    
    # 3. Read the fixed-width file using the extracted lists
    # We use dtype=str to ensure codes (like IBGE geographic codes) don't lose leading zeros
    df_pnad = pd.read_fwf(
        file_path, 
        widths=sizes, 
        names=variables, 
        dtype=str 
    )
    
    # 4. Return the structured dataframe
    return df_pnad