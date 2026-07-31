import os
import pandas as pd
import numpy as np


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

def create_family_id(df):
    """
    Cleans identification columns and creates a 'FamilyID' column.
    
    Parameters:
    df (pandas.DataFrame): The input dataframe containing PNAD data.
    
    Returns:
    pandas.DataFrame: A new dataframe with the new 'FamilyID'.
    """
    # 1. Create a copy of the dataframe to avoid modifying the original data directly
    df_clean = df.copy()
    
    # 2. Define the columns needed for the ID
    columns_for_id = ['UPA', 'V1008', 'V1014', 'V2003']
    
    # 3. Loop through the columns to convert to string and remove '.0'
    for col in columns_for_id:
        # Check if column exists to avoid errors
        if col in df_clean.columns: 
            df_clean[col] = df_clean[col].astype(str).str.replace(r'\.0$', '', regex=True)
            
    # 4. Create the FamilyID by concatenating the necessary string columns
    df_clean['FamilyID'] = df_clean['UPA'] + df_clean['V1008'] + df_clean['V1014']

    # 5. Replace df index
    df_clean.set_index('FamilyID', inplace=True)
    
    # 6. Return the modified dataframe
    return df_clean

def classify_tenure_condition(df):
    """
    Classifies housing tenure into four categories.
    
    Parameters:
    df (pandas.DataFrame): The input dataframe containing PNAD housing variables.
    
    Returns:
    pandas.DataFrame: A new dataframe with the added categorical 'tenure_condition' column.
    """
    import numpy as np
    
    # 1. Create a copy to protect the original dataframe
    df_clean = df.copy()
    
    # 2. Ensure the required columns are strings and remove any float artifacts
    cols_to_str = ['S01001', 'S01017', 'S01020', 'S01020A']
    for col in cols_to_str:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.replace(r'\.0$', '', regex=True)
            
    # 3. Define the conditions
    # i) Proprietários formais
    cond_prop_formal = (
        (df_clean['S01017'].isin(['1', '2'])) & 
        (df_clean['S01020'] == '1') & 
        (df_clean['S01020A'] == '1')
    )

    # ii) Inquilinos formais
    cond_inq_formal = (
        (df_clean['S01001'].isin(['1', '2'])) & 
        (df_clean['S01017'].isin(['3', '4', '5', '6']))
    )

    # iii) Proprietários informais
    cond_prop_informal = (
        (df_clean['S01017'].isin(['1', '2'])) & 
        ((df_clean['S01020'] == '2') | (df_clean['S01020A'] == '2'))
    )

    # iv) Inquilinos informais
    cond_inq_informal = (
        (df_clean['S01001'] == '3') & 
        (df_clean['S01017'].isin(['3', '4', '5', '6']))
    )

    # 4. Group the conditions and their corresponding category labels
    conditions = [cond_prop_formal, cond_inq_formal, cond_prop_informal, cond_inq_informal]
    choices = ['Proprietário Formal', 'Inquilino Formal', 'Proprietário Informal', 'Inquilino Informal']

    # 5. Apply numpy.select to create the new 'option' column
    df_clean['tenure_condition'] = np.select(conditions, choices, default='Outros')
    
    # 6. Return the updated dataframe
    return df_clean

def generate_tenure_table(df, tenure_col='tenure_condition', weight_col='weight_expansion'):
    """
    Generates a formatted frequency table for tenure conditions
    """
    # 1. Calculate raw frequencies
    freqs = df.groupby(tenure_col)[weight_col].sum()
    
    # 2. Define Valid categories and Missing category
    valid_mapping = {
        'Proprietário Formal': 'Proprietário Formal',
        'Inquilino Formal': 'Inquilino Formal',
        'Proprietário Informal': 'Proprietário Informal',
        'Inquilino Informal': 'Inquilino Informal'
    }
    
    # 3. Separate frequencies into Valid and Missing
    valid_freqs = {display_name: freqs.get(data_name, 0) for data_name, display_name in valid_mapping.items()}
    missing_freq = freqs.get('Outros', 0)
    
    total_valid = sum(valid_freqs.values())
    grand_total = total_valid + missing_freq
    
    # 4. Build the rows step-by-step
    rows = []
    cum_pct = 0.0
    
    # A. Add Valid categories
    for category, freq in valid_freqs.items():
        pct = (freq / grand_total) * 100 if grand_total > 0 else 0
        valid_pct = (freq / total_valid) * 100 if total_valid > 0 else 0
        cum_pct += valid_pct
        
        rows.append({
            'Level_1': 'Válido',
            'Condição de ocupação': category,
            'Frequência': freq,
            'Percentual': pct,
            'Percentual válido': valid_pct,
            'Percentual acumulado': cum_pct
        })
        
    # B. Add Total Valid row
    rows.append({
        'Level_1': 'Válido',
        'Condição de ocupação': 'Total',
        'Frequência': total_valid,
        'Percentual': (total_valid / grand_total) * 100 if grand_total > 0 else 0,
        'Percentual válido': 100.0,
        'Percentual acumulado': np.nan 
    })
    
    # C. Add Missing row
    rows.append({
        'Level_1': 'Faltante',
        'Condição de ocupação': '',
        'Frequência': missing_freq,
        'Percentual': (missing_freq / grand_total) * 100 if grand_total > 0 else 0,
        'Percentual válido': np.nan,
        'Percentual acumulado': np.nan
    })
    
    # D. Add Grand Total row
    rows.append({
        'Level_1': 'Total',
        'Condição de ocupação': '',
        'Frequência': grand_total,
        'Percentual': 100.0,
        'Percentual válido': np.nan,
        'Percentual acumulado': np.nan
    })
    
    # 5. Convert to DataFrame
    df_table = pd.DataFrame(rows)
    
    # 6. Set the MultiIndex to create the visual grouping effect
    df_table.set_index(['Level_1', 'Condição de ocupação'], inplace=True)
    df_table.index.names = [None, 'Condição de ocupação'] # Hide the 'Level_1' label
    
    # 7. Format the output 
    format_dict = {
        'Frequência': '{:,.0f}',
        'Percentual': '{:.1f}',
        'Percentual válido': '{:.1f}',
        'Percentual acumulado': '{:.1f}'
    }
    
    # Create a styled dataframe 
    styled_table = df_table.style.format(format_dict, na_rep="")
    
    return styled_table