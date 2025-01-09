import streamlit as st
import pandas as pd
from sqlmodel import SQLModel, Field
from typing import Any, Dict, Type
from datetime import datetime

def generate_sqlmodel_class(df: pd.DataFrame, class_name: str) -> Type[SQLModel]:
    class_dict = {
        "__tablename__": class_name.lower(),
        "__table_args__": {'extend_existing': True},
        "id": (int, Field(default=None, primary_key=True))
    }
    
    for column in df.columns:
        dtype = df[column].dtype
        if dtype == 'int64':
            class_dict[column] = (int, Field(default=0))
        elif dtype == 'float64':
            class_dict[column] = (float, Field(default=0.0))
        elif dtype == 'bool':
            class_dict[column] = (bool, Field(default=False))
        elif dtype == 'datetime64[ns]':
            class_dict[column] = (datetime, Field(default_factory=datetime.now))
        else:
            class_dict[column] = (str, Field(default=""))
    
    # Correctly annotate the fields
    for key, (field_type, field_info) in class_dict.items():
        if key not in ["__tablename__", "__table_args__"]:
            class_dict[key] = field_type(**field_info._asdict())
    
    return type(class_name, (SQLModel,), class_dict)

st.title("Excel to SQLModel Model Generator")

uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.write("DataFrame preview:")
    st.dataframe(df.head())
    
    class_name = st.text_input("Enter the class name for the SQLModel model", "Data")
    
    if st.button("Generate SQLModel Model"):
        model_class = generate_sqlmodel_class(df, class_name)
        st.write(f"Generated SQLModel class `{class_name}`:")
        st.code(model_class.__dict__)