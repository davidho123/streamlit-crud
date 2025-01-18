# Streamlit-Crud

**Automatically generate UI interfaces and implement CRUD functions**

![CRUD主界面](home.png)\
![新增表单](creat.png)\
![修改表单](modify.png)

## Table of Contents
* [Overview](README.md##1.Overview)
* [Features](README.md##2.Features)
* [Usage](README.md##3.Usage)
* [Version Information](README.md##4.VersionInformation)

## 1. Overview
This module is a class that automatically generates form components and CRUD buttons based on the database model. After the form is submitted, it implements the CRUD functions of the database.
## 2. Features
- Dynamically generate form components based on the database model.\
The form components are dynamically generated according to the field types of the model.
- Generate CRUD buttons, and after submission, implement the CRUD functions of the database.
- The database is displayed in a dataframe table, which is equipped with filtering, searching, pagination, and downloading functions.
- Add a log folder in the root directory, create a log file with the current date, and record the information of adding, deleting, modifying, and querying.
>Note: The newly added table export generates the file name based on local time.\
>The download of the streamlit table uses UTC time. Therefore, this export function is added.

## 3. Usage
- Install the required packages
```Python
pip install streamlit_crud
pip install streamlit sqlmodel streamlit_antd_components pandas
```
UI component generation uses streamlit
Database model uses sqlmodel
Table pagination function uses streamlit_antd_components
Table filtering uses pandas
- Usage example

**The StreamlitCrud class requires two parameters, the first is the database model class, and the second is the database connection address.**\
**Run the main method of StreamlitCrud to generate the UI interface and implement CRUD functions.**

>Note:\
>1.In the database model class, when the field name is "Remarks", a multi-line text component will be used.\
>2.The initial value of the form component is initialized according to the default value of the model field.\
>3.In the creat and modify forms, each item in the form is a required field, and an error will be prompted if it is not filled in.\
>4.Select the wide mode, otherwise the buttons will be cramped together\
> st.set_page_config(layout="wide")

```Python
import streamlit as st
from sqlmodel import SQLModel, Field
from streamlit_crud.class_crud import StreamlitCrud
from datetime import date, datetime

# Define the database model class
class Data(SQLModel, table=True):
    __tablename__ = "data"
    __table_args__ = {'extend_existing': True}
    id: int = Field(default=None, primary_key=True,
                    sa_column_kwargs={"autoincrement": True})
    Name: str = Field(default="")
    Price: float = Field(default=0.0)
    In_Stock: bool = Field(default=True)
    Entry_Date: date = Field(default=date.today())
    Entry_Time: str = Field(default=datetime.now().strftime('%H:%M:%S'))
    Remarks: str = Field(default="None")  # The remarks attribute will use a multi-line text component

database_url = "sqlite:///example.db"
# Select the wide mode, otherwise the buttons will be cramped together.
st.set_page_config(page_title="数据管理系统",  layout="wide")
stcrud = StreamlitCrud(Data, database_url)
stcrud.main()
```
## 4. Version Information
v 0.1
Provides the class module to implement the CRUD functions of the database.
