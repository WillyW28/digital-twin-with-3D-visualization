def obtain_max(result_data):
    # Find the row with the maximum value in the result column 
    max_row = result_data.loc[result_data.iloc[:, 3].idxmax()]
    
    # Extract location (columns 1, 2, and 3) and the result (column 4)
    max_location = max_row.iloc[:3].tolist()  # Convert to list for easier handling
    max_result = max_row.iloc[3]
   
    max_result_info = {
        'points': max_location,
        'result': max_result
    } 
    
    return max_result_info


def obtain_min(result_data):
    # Find the row with the maximum value in the result column 
    min_row = result_data.loc[result_data.iloc[:, 3].idxmin()]
    
    # Extract location (columns 1, 2, and 3) and the result (column 4)
    min_location = min_row.iloc[:3].tolist()  # Convert to list for easier handling
    min_result = min_row.iloc[3]
   
    min_result_info = {
        'points': min_location,
        'result': min_result
    } 
    
    return min_result_info