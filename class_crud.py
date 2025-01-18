"""
根据数据库模型类，动态生成表单字段，并校验输入是否为空（排除布尔值字段）并转换数据类型。
内容：
1、增删改查按钮,点击后弹出操作表单
2、筛选过滤框
3、数据显示
4、弹窗内，名称和组件分开，同行显示，且名称前加红色星号
5、样式：减去顶部空间，调整body外边距

author: davidho
date: 2025-01-09
version: 0.1
"""
import os

import streamlit as st
from sqlmodel import SQLModel, Field, create_engine, Session, select, inspect
from datetime import date, datetime
import streamlit_antd_components as sac
import logging
import pandas as pd
from zoneinfo import ZoneInfo  


# 定义数据库模型类
class Data(SQLModel, table=True):
    __tablename__ = "data"
    __table_args__ = {'extend_existing': True}
    id: int = Field(default=None, primary_key=True,
                    sa_column_kwargs={"autoincrement": True})
    名称: str = Field(default="")
    名称: str = Field(default="")
    价格: float = Field(default=0.0)
    有货: bool = Field(default=True)
    录入日期: date = Field(default=date.today())
    录入时间: str = Field(default=datetime.now().strftime('%H:%M:%S'))
    备注: str = Field(default="无")  # 备注属性会使用多行文字组件


class StreamlitCRUD:
    def __init__(self, model_class, database_url):
        self.model_class = model_class
        self.database_url = database_url
        self.engine = self.create_database_engine(database_url)
        self.model_attributes, self.model_name = self.get_model_attributes(model_class)
        self.configure_logging()

    def configure_logging(self):
        # 确保 log 文件夹存在
        log_folder = 'log'
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
        # 动态生成日志文件名，以当前日期命名
        log_filename = f'{log_folder}/crud_{date.today().strftime("%Y-%m-%d")}.log'
        logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def create_database_engine(self, database_url):
        engine = create_engine(database_url)
        SQLModel.metadata.create_all(engine)
        return engine

    def get_model_attributes(self, model_class):
        attributes = {}
        for field_name, field_info in model_class.__fields__.items():
            if field_name == "id":  # 跳过主键字段
                continue
            attributes[field_name] = {
                "type": field_info.annotation,
                "default": field_info.default_factory() if callable(field_info.default_factory) else field_info.default
            }
        return attributes, model_class.__name__

    def generate_form_fields(self, initial_values=None, disabled=False, button_label='提交'):
        form_data = {}
        form_key = f"data_form_{self.model_name}"
        with st.form(key=form_key):
            i=0
            for attr_name, attr_info in self.model_attributes.items():
                i += 1
                attr_type = attr_info["type"]
                if initial_values:
                    default_value = initial_values.get(attr_name, attr_info["default"])
                else:
                    default_value = attr_info["default"]
            
                # 添加标签
                row_input = st.columns([1, 4])
                row_input[0].container(key=f"title{i}").markdown(f":red[*]{attr_name}")
                st.html("<style>.st-key-title%d {position: absolute; top: 10px;}</style>"%i)
                with row_input[1]:
                    if attr_name == "entry_time":
                        value = st.text_input(attr_name, value=default_value, key=f"{form_key}_{attr_name}", disabled=disabled,label_visibility="collapsed")
                    elif attr_name == "备注":
                        value = st.text_area(attr_name, value=default_value, key=f"{form_key}_{attr_name}", disabled=disabled,label_visibility="collapsed")
                    elif attr_type == int:
                        value = st.number_input(attr_name, step=1, value=default_value, key=f"{form_key}_{attr_name}", disabled=disabled, label_visibility="collapsed")
                    elif attr_type == float:
                        value = st.number_input(attr_name, format="%f", value=default_value, key=f"{form_key}_{attr_name}", disabled=disabled, label_visibility="collapsed")
                    elif attr_type == bool:
                        value = st.checkbox(attr_name, value=default_value, key=f"{form_key}_{attr_name}", disabled=disabled, label_visibility="collapsed")
                    elif attr_type == str:
                        value = st.text_input(attr_name, value=default_value, key=f"{form_key}_{attr_name}", disabled=disabled, label_visibility="collapsed")
                    elif attr_type == date:
                        value = st.date_input(attr_name, value=default_value, key=f"{form_key}_{attr_name}", disabled=disabled, label_visibility="collapsed")
                    else:
                        value = st.text_input(attr_name, value=default_value, key=f"{form_key}_{attr_name}", disabled=disabled, label_visibility="collapsed")
                    form_data[attr_name] = value
        
            submit_button = st.form_submit_button(label=button_label)
        return form_data, submit_button

    def validate_and_convert_form_data(self, form_data):
        valid = True
        converted_data = {}
        
        for attr_name, value in form_data.items():
            if not value and self.model_attributes[attr_name]["type"] != bool:
                st.error(f"{attr_name} 字段不能为空")
                valid = False
            else:
                attr_type = self.model_attributes[attr_name]["type"]
                if attr_type == int:
                    converted_data[attr_name] = int(value)
                elif attr_type == float:
                    converted_data[attr_name] = float(value)
                elif attr_type == bool:
                    converted_data[attr_name] = bool(value)
                elif attr_type == date:
                    converted_data[attr_name] = value
                else:
                    converted_data[attr_name] = value
        
        return valid, converted_data

    def handle_add_submission(self):
        # 获取模型的初始属性值
        form_data, submit_button = self.generate_form_fields(button_label='提交')
        if submit_button:
            # 校验表单数据并转换数据类型
            valid, converted_data = self.validate_and_convert_form_data(form_data)
            
            if valid:
                new_data = self.model_class(**converted_data)
                with Session(self.engine) as session:
                    session.add(new_data)
                    session.commit()
                logging.info(f"新增数据: {converted_data}")
                st.html("<style>.stDialog {display: None;}</style>")           
                st.toast("数据已成功录入！")
            else:
                st.error("请填写完整表单")

    def handle_update_submission(self, data_id, form_data):
        valid, converted_data = self.validate_and_convert_form_data(form_data)
        
        if valid:
            with Session(self.engine) as session:
                data_to_update = session.exec(select(self.model_class).where(self.model_class.id == data_id)).first()
                if data_to_update:
                    for attr_name, value in converted_data.items():
                        setattr(data_to_update, attr_name, value)
                    session.commit()
                    logging.info(f"更新数据: ID {data_id}, 新数据: {converted_data}")
                else:
                    st.error(f"数据 ID {data_id} 未找到")

    def delete_data(self, data_id):
        with Session(self.engine) as session:
            data_to_delete = session.exec(select(self.model_class).where(self.model_class.id == data_id)).first()
            if data_to_delete:
                session.delete(data_to_delete)
                session.commit()
                logging.warning(f"删除数据: ID {data_id},被删除数据：{data_to_delete}")
            else:
                st.error(f"数据 ID {data_id} 未找到")

    def modify_data(self, data_id):
        # st.title(f"修改数据信息 (ID: {data_id})")
        
        with Session(self.engine) as session:
            data_entry = session.exec(select(self.model_class).where(self.model_class.id == data_id)).first()
            if data_entry:
                initial_values = {field: getattr(data_entry, field) for field in self.model_attributes.keys()}
            else:
                st.error(f"数据 ID {data_id} 未找到")
                return
        
        form_data, submit_button = self.generate_form_fields(initial_values)
        
        if submit_button:
            self.handle_update_submission(data_id, form_data)
            st.html("<style>.stDialog {display: None;}</style>")
            st.toast(f"数据 ID {data_id} 已成功更新！")

    def delete_data_with_confirmation(self, data_id):
        # st.title(f"删除数据信息 (ID: {data_id})")
        
        with Session(self.engine) as session:
            data_entry = session.exec(select(self.model_class).where(self.model_class.id == data_id)).first()
            if data_entry:
                initial_values = {field: getattr(data_entry, field) for field in self.model_attributes.keys()}
            else:
                st.error(f"数据 ID {data_id} 未找到")
                return
        
        _, submit_button = self.generate_form_fields(initial_values, disabled=True, button_label='删除')
        
        if submit_button:
            self.delete_data(data_id)
            st.html("<style>.stDialog {display: None;}</style>")
            st.toast(f"数据 ID {data_id} 已成功删除！")

    def view_data_by_id(self, data_id):
        # st.title(f"查看数据信息 (ID: {data_id})")
        
        with Session(self.engine) as session:
            data_entry = session.exec(select(self.model_class).where(self.model_class.id == data_id)).first()
            if data_entry:
                initial_values = {field: getattr(data_entry, field) for field in self.model_attributes.keys()}
            else:
                st.error(f"数据 ID {data_id} 未找到")
                return
        
        _, submit_button = self.generate_form_fields(initial_values, disabled=True, button_label='确定')
        
        if submit_button:
            st.rerun()

    def query_all_data(self):
        with Session(self.engine) as session:
            data_entries = session.exec(select(self.model_class)).all()
        inspector = inspect(self.model_class)
        columns = [column.name for column in inspector.columns]
        logging.info(f"查询所有数据: {len(data_entries)} 条记录") 
        return data_entries, columns

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
        st.dataframe(data_current_page, height=height-15, hide_index=True, use_container_width=True)
        sac.pagination(total=len(df), page_size=limit, align='center', jump=True, show_total=True, key='curpage_u')

    def display_data(self):
        data_entries, columns = self.query_all_data()
        if not data_entries:
            st.info("暂无数据信息")
        else:
            df = pd.DataFrame([data_entry.dict() for data_entry in data_entries], columns=columns)
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
            
            limit = 10
            height = 402
            beijingtime = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
            row_select[5].download_button("⬇️导出下表数据", data=filtered_df.to_csv(index=False),
                                        file_name=f"{beijingtime}data.csv", mime="text/csv")
            
            self.data_pages(df=filtered_df, limit=limit, height=height)

    @st.fragment
    def style(self):
        st.html("""<style>
                [data-testid="stHeader"] {
                    height: 1px;
                }
                
                .block-container { 
                    padding: 20px 50px;
                }

                .stSidebar  {
                    width: 250px;
                }

            </style>
            """)
    
    @st.fragment
    def style2(self):
        st.html("""<style>
                .stButton > button {
                min-height: 100%;
                min-width: 100%;
                width: max-content;
                    }
                .stToast {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%); 
                    z-index: 9999;
                    background-color: #FFFACD;
                    font-weight: 800;
                }
            </style>
            """)

    def main(self):
        self.style()
        self.style2()

        def data_id_input():
            row_input = st.columns([1, 2,1])
            row_input[0].container(key="data_id_input").markdown("**请输入数据ID**")
            st.html("<style>.st-key-data_id_input {position: absolute; top: 8px;}</style>")
            data_id = row_input[1].number_input("请输入数据ID", min_value=1, step=1,label_visibility="collapsed")
            return data_id

        st.subheader("数据管理")
        with st.container(key="add_button"):
            rows = st.columns([1, 1, 1, 1, 10])
            if rows[0].button(":material/add:新增"):
                @st.dialog("新增数据")
                def dialog_add_data():
                    self.handle_add_submission()
                dialog_add_data()
            if rows[1].button(":material/edit:修改"):
                @st.dialog("修改数据")
                def dialog_modify_data():
                    data_id = data_id_input()
                    self.modify_data(data_id)
                dialog_modify_data()
            if rows[2].button(":material/search:查看"):
                @st.dialog("查看数据")
                def dialog_view_data():
                    data_id = data_id_input()
                    self.view_data_by_id(data_id)
                dialog_view_data()
            if rows[3].button(":material/delete:删除", type="primary"):
                @st.dialog("删除数据")
                def dialog_delete_data():
                    data_id = data_id_input()
                    self.delete_data_with_confirmation(data_id)
                dialog_delete_data()
        
        self.display_data()

if __name__ == "__main__":
    st.set_page_config(page_title="数据管理系统", page_icon=":material/database:", layout="wide")
    stcrud = StreamlitCRUD(Data, "sqlite:///example.db")
    stcrud.main()
    
    

