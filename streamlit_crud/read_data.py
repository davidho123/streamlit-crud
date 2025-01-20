"""
筛选过滤数据库工具
1、输入数据库地址
2、侧边栏选择数据库的表
3、中心区有初次过滤，下方显示过滤后数据
4、详情按钮，对初次过滤的数据，根据id进行二次过滤，然后选择显示的数据

author: davidho
date: 2025-01-20
version: 0.1.6
"""

import streamlit as st
from datetime import datetime
from sqlmodel import SQLModel, create_engine, inspect
import streamlit_antd_components as sac
import pandas as pd

class ReadData():
    """
    :param database_url:str
    根据数据库地址，过滤并显示数据
    """

    def __init__(self, database_url):
        self.database_url = database_url
        self.engine = self.create_database_engine(database_url)
        self.table_name = self.get_tables()

    def create_database_engine(self, database_url):
        engine = create_engine(database_url)
        SQLModel.metadata.create_all(engine)
        return engine

    def get_tables(self):
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        selected_table = st.sidebar.selectbox('选择数据库表', tables)
        return selected_table

    def read_table_to_df(self):
        with self.engine.connect() as connection:
            df = pd.read_sql(self.table_name, connection)
        return df

    def data_pages(self, df, limit=10, height=402):
        if "curpage_u" not in st.session_state:
            st.session_state.curpage_u = 1

        if "current_page_u" not in st.session_state:
            st.session_state["current_page_u"] = 1
        else:
            st.session_state["current_page_u"] = st.session_state.curpage_u
        current_page = st.session_state.current_page_u

        limit = limit
        data_current_page = df[(int(current_page) - 1) * int(limit):(int(current_page) * int(limit))]
        st.dataframe(data_current_page, height=height, hide_index=True, use_container_width=True)
        sac.pagination(total=len(df), page_size=limit, align='center', jump=True, show_total=True, key='curpage_u')

    @st.fragment
    def style(self):
        st.html("""<style>
                [data-testid="stHeader"] {
                    height: 1px;
                }

                .block-container { 
                    padding: 20px 50px;
                }
            </style>
            """)

    @st.dialog(title="数据详情",width="large")
    def show_detail(self, df):
        # id_column = st.selectbox('选择过滤列', df.columns)
        id_value = st.selectbox('选择id值', df["id"])
        if id_value:
            id_df = df[df["id"] == id_value]
            if id_df.empty:
                st.info("未找到对应ID的数据")
            else:
                selected_columns = st.multiselect('选择要显示的列', id_df.columns, default=None)
                for column in selected_columns:
                    st.text_area(f"{column} 数据", value=id_df[column].to_string(index=False), height=150)

    def main(self):
        self.style()
        if self.table_name:
            df = self.read_table_to_df()
            if df.empty:
                st.info("暂无数据信息")
            else:
                row_select = st.columns([2, 2, 0.5, 2, 1.6, 1.5])
                search_columns = row_select[0].selectbox('选择要筛选的列', df.columns)
                search = row_select[1].text_input('输入筛选文字 ')
                row_select[2].button(':material/search:', key="search_btn")
                st.html("<style>.st-key-search_btn {position: absolute; top: 30px;}</style>")

                df = df.astype(str)
                filtered_df = df[df[search_columns].str.contains(search, case=False)]

                with row_select[3].popover("选择要显示的列"):
                    select_columns = st.multiselect('选择要显示的列', df.columns, default=df.columns)
                st.html("<style>.stPopover {position: absolute; top: 25px;}</style>")
                filtered_df = filtered_df[select_columns]

                limit = 15
                height = 562
                beijingtime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row_select[5].download_button("⬇️导出下表数据", data=filtered_df.to_csv(index=False),
                                              file_name=f"{beijingtime}data.csv", mime="text/csv")

                # 增加详情按钮
                if row_select[4].button("二次筛选",key="detail_button"):
                    self.show_detail(filtered_df)

                self.data_pages(df=filtered_df, limit=limit, height=height)
        else:
            st.info("请选择一个表")



if __name__ == '__main__':
    database_url = "sqlite:///example.db"
    st.set_page_config(page_title="数据查阅系统", page_icon=":material/database:", layout="wide")
    read = ReadData(database_url)
    read.main()