import pandas as pd

def clean_data(df,mode=1, meta_stability_cutoff = 5000,N=100000):
    """
    Clean the given DataFrame by processing the Meta Stability column.
    
    Parameters:
        df (pandas.DataFrame): The DataFrame to be cleaned.
        mode (int, optional): Mode 1 for ddmtd 1 and Mode 2 for ddmtd 2
        meta_stability_cutoff (int, optional): The cutoff value for categorizing Meta Stability. Defaults to 20000. Best to set it quater of the N value!
    
    Returns:
        pandas.DataFrame: The cleaned DataFrame with additional columns for falling edge, average, minimum, maximum, maximum-minimum, and count.
    """
    #Cleaning up the first values...
    # print(df.ddmtd.values[0]%(N))
    # df.ddmtd = df.ddmtd #- df.ddmtd.values[0]%(N/2)

    #Cleaning up Meta Stability
    #Categorizing Meta Stability into bins
    df["ddmtd_diff"] = df.ddmtd.diff()
    df["meta_sec"]  = df.ddmtd_diff.where(df.ddmtd_diff > meta_stability_cutoff,0)
    df["meta_sec"]  = df.meta_sec.where(df.meta_sec < meta_stability_cutoff,1)
    df["meta_sec"]  = df.meta_sec.cumsum() # tagging each metastability with a number that with the cumulative sum trick


    # display(df.head(30))
    min_value = df.reset_index(drop=True).set_index("meta_sec").ddmtd.groupby("meta_sec").min()
    max_value = df.reset_index(drop=True).set_index("meta_sec").ddmtd.groupby("meta_sec").max()
    count = df.reset_index(drop=True).set_index("meta_sec").ddmtd.groupby("meta_sec").count()
    avg = df.reset_index(drop=True).set_index("meta_sec").ddmtd.groupby("meta_sec").mean()
    #Fixing Edge:: 1--> High to Low transition, 0--> Low to High transition
    last = df.set_index("meta_sec").edge.groupby("meta_sec").last()





    cleaned_df = pd.DataFrame()
    cleaned_df[f"falling_edge{mode}"] = last
    cleaned_df[f"avg{mode}"] = avg
    cleaned_df[f"min{mode}"] = min_value
    cleaned_df[f"max{mode}"] = max_value
    cleaned_df[f"max_min{mode}"] = max_value - min_value
    cleaned_df[f"count{mode}"] = count
    return cleaned_df