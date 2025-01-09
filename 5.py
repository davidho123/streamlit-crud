"""
根据数据库模型类，动态生成表单字段，并校验输入是否为空（排除布尔值字段）并转换数据类型。
内容：
1、增删改查按钮,点击后弹出操作表单
2、筛选框
3、数据显示

author: davidho
date: 2025-01-09
version: 0.1
"""


import streamlit as st
from sqlmodel import SQLModel, Field, create_engine, Session, select, inspect
from datetime import date, datetime
import time
import streamlit_antd_components as sac
import logging
import pandas as pd
from zoneinfo import ZoneInfo  


# 定义数据库模型类
class Data(SQLModel, table=True):
    __tablename__ = "data"
    __table_args__ = {'extend_existing': True}
    id: int = Field(default=None, primary_key=True)
    name: str = Field(default="")
    value: float = Field(default=0.0)
    active: bool = Field(default=True)
    entry_date: date = Field(default=date.today())
    entry_time: str = Field(default=datetime.now().strftime('%H:%M:%S'))
    description: str = Field(default="")  # 新增的介绍属性

# 配置日志记录
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 创建数据库引擎并创建表
def create_database_engine(database_url):
    engine = create_engine(database_url)
    SQLModel.metadata.create_all(engine)
    return engine

# 获取模型的属性名称、类型和默认值
def get_model_attributes(model_class):
    attributes = {}
    for field_name, field_info in model_class.__fields__.items():
        if field_name == "id":  # 跳过主键字段
            continue
        attributes[field_name] = {
            "type": field_info.annotation,
            "default": field_info.default_factory() if callable(field_info.default_factory) else field_info.default
        }
    return attributes, model_class.__name__

# 动态生成表单字段
def generate_form_fields(model_attributes, model_name, initial_values=None, disabled=False, button_label='提交'):
    form_data = {}
    form_key = f"data_form_{model_name}"
    with st.form(key=form_key):
        for attr_name, attr_info in model_attributes.items():
            attr_type = attr_info["type"]
            if initial_values:
                default_value = initial_values.get(attr_name, attr_info["default"])
            else:
                default_value = attr_info["default"]
            
            if attr_name == "entry_time":
                value = st.text_input(attr_name, value=default_value, key=f"{form_key}_{attr_name}", disabled=disabled)
            elif attr_name == "description":
                value = st.text_area(attr_name, value=default_value, key=f"{form_key}_{attr_name}", disabled=disabled)
            elif attr_type == int:
                value = st.number_input(attr_name, step=1, value=default_value, key=f"{form_key}_{attr_name}", disabled=disabled)
            elif attr_type == float:
                value = st.number_input(attr_name, format="%f", value=default_value, key=f"{form_key}_{attr_name}", disabled=disabled)
            elif attr_type == bool:
                value = st.checkbox(attr_name, value=default_value, key=f"{form_key}_{attr_name}", disabled=disabled)
            elif attr_type == str:
                value = st.text_input(attr_name, value=default_value, key=f"{form_key}_{attr_name}", disabled=disabled)
            elif attr_type == date:
                value = st.date_input(attr_name, value=default_value, key=f"{form_key}_{attr_name}", disabled=disabled)
            else:
                value = st.text_input(attr_name, value=default_value, key=f"{form_key}_{attr_name}", disabled=disabled)
            form_data[attr_name] = value
        
        submit_button = st.form_submit_button(label=button_label)
    return form_data, submit_button

# 校验输入是否为空（排除布尔值字段）并转换数据类型
def validate_and_convert_form_data(form_data, model_attributes):
    valid = True
    converted_data = {}
    
    for attr_name, value in form_data.items():
        if not value and model_attributes[attr_name]["type"] != bool:
            st.error(f"{attr_name} 字段不能为空")
            valid = False
        else:
            attr_type = model_attributes[attr_name]["type"]
            if attr_type == int:
                converted_data[attr_name] = int(value)
            elif attr_type == float:
                converted_data[attr_name] = float(value)
            elif attr_type == bool:
                converted_data[attr_name] = bool(value)
            elif attr_type == date:
                converted_data[attr_name] = value
            # elif attr_type == time:
            #     converted_data[attr_name] = time.fromisoformat(value.strftime('%H:%M:%S'))
            else:
                converted_data[attr_name] = value
    
    return valid, converted_data

# 处理表单提交逻辑（新增）
def handle_add_submission(form_data, model_attributes, model_class, engine):
    valid, converted_data = validate_and_convert_form_data(form_data, model_attributes)
    
    if valid:
        new_data = model_class(**converted_data)
        with Session(engine) as session:
            session.add(new_data)
            session.commit()
        # st.success(f"{converted_data['name']} 已成功录入！")
        logging.info(f"新增数据: {converted_data}")

# 处理表单提交逻辑（修改）
def handle_update_submission(data_id, form_data, model_attributes, model_class, engine):
    valid, converted_data = validate_and_convert_form_data(form_data, model_attributes)
    
    if valid:
        with Session(engine) as session:
            data_to_update = session.exec(select(model_class).where(model_class.id == data_id)).first()
            if data_to_update:
                for attr_name, value in converted_data.items():
                    setattr(data_to_update, attr_name, value)
                session.commit()
                # st.success(f"数据 ID {data_id} 已成功更新！")
                logging.info(f"更新数据: ID {data_id}, 新数据: {converted_data}")
            else:
                st.error(f"数据 ID {data_id} 未找到")

# 删除数据信息
def delete_data(data_id,model_class, engine):
    with Session(engine) as session:
        data_to_delete = session.exec(select(model_class).where(model_class.id == data_id)).first()
        if data_to_delete:
            session.delete(data_to_delete)
            session.commit()
            # st.success(f"数据 ID {data_id} 已成功删除！")
            logging.info(f"删除数据: ID {data_id},被删除数据：{data_to_delete}")
        else:
            st.error(f"数据 ID {data_id} 未找到")



# 修改数据信息
def modify_data(data_id, model_attributes, model_class, engine):
    st.title(f"修改数据信息 (ID: {data_id})")
    
    # 查询现有数据信息
    with Session(engine) as session:
        data_entry = session.exec(select(model_class).where(model_class.id == data_id)).first()
        if data_entry:
            initial_values = {field: getattr(data_entry, field) for field in model_attributes.keys()}
        else:
            st.error(f"数据 ID {data_id} 未找到")
            return
    
    # 动态生成表单字段
    form_data, submit_button = generate_form_fields(model_attributes, model_class.__name__, initial_values)
    
    # 处理表单提交逻辑
    if submit_button:
        handle_update_submission(data_id, form_data, model_attributes, model_class, engine)
        st.html("<style>.stDialog {display: None;}</style>")
        st.toast(f"数据 ID {data_id} 已成功更新！")

# 删除数据信息并显示确认表单
def delete_data_with_confirmation(data_id, model_attributes, model_class, engine):
    st.title(f"删除数据信息 (ID: {data_id})")
    
    # 查询现有数据信息
    with Session(engine) as session:
        data_entry = session.exec(select(model_class).where(model_class.id == data_id)).first()
        if data_entry:
            initial_values = {field: getattr(data_entry, field) for field in model_attributes.keys()}
        else:
            st.error(f"数据 ID {data_id} 未找到")
            return
    
    # 动态生成表单字段（只读模式）
    _, submit_button = generate_form_fields(model_attributes, model_class.__name__, initial_values, disabled=True, button_label='删除')
    
    # 处理删除逻辑
    if submit_button:
        delete_data(data_id,model_class, engine)
        st.html("<style>.stDialog {display: None;}</style>")
        st.toast(f"数据 ID {data_id} 已成功删除！")

# 按照ID查看数据信息
def view_data_by_id(data_id, model_attributes, model_class, engine):
    st.title(f"查看数据信息 (ID: {data_id})")
    
    # 查询现有数据信息
    with Session(engine) as session:
        data_entry = session.exec(select(model_class).where(model_class.id == data_id)).first()
        if data_entry:
            initial_values = {field: getattr(data_entry, field) for field in model_attributes.keys()}
        else:
            st.error(f"数据 ID {data_id} 未找到")
            return
    
    # 动态生成表单字段（只读模式）
    _, submit_button = generate_form_fields(model_attributes, model_class.__name__, initial_values, disabled=True, button_label='确定')
    
    # 返回按钮
    if submit_button:
        st.rerun()

# 查询所有数据信息
def query_all_data(model_class, engine):
    with Session(engine) as session:
        data_entries = session.exec(select(model_class)).all()
    # 获取表的元数据
    inspector = inspect(model_class)
    # 获取列的顺序
    columns = [column.name for column in inspector.columns]
    logging.info(f"查询所有数据: {len(data_entries)} 条记录") 
    return data_entries,columns

# 分页显示数据信息
def data_pages(df,limit=10,height=402):
    if "curpage_u" not in st.session_state:
        st.session_state.curpage_u = 1


    if "current_page_u" not in st.session_state:
        st.session_state["current_page_u"] = 1
    else:
        st.session_state["current_page_u"] = st.session_state.curpage_u
    current_page = st.session_state.current_page_u


    limit = limit
    data_current_page = df[(int(current_page) - 1) * int(limit):(int(current_page) * int(limit))]
    # with st.container(height=height, border=False):
    st.dataframe(data_current_page,height=height-15, hide_index=True, use_container_width=True)
    sac.pagination(total=len(df), page_size=limit, align='center', jump=True, show_total=True, key='curpage_u')

# 显示所有数据信息
def display_data(model_class, engine):
    data_entries,columns = query_all_data(model_class, engine)
    if not data_entries:
        st.info("暂无数据信息")
    else:
        df = pd.DataFrame([data_entry.dict() for data_entry in data_entries], columns=columns)
        row_select = st.columns([2, 2, 0.5, 2,1.6, 1.5])
        search_columns = row_select[0].selectbox('选择要筛选的列', df.columns)
        search = row_select[1].text_input('输入筛选文字 ')
        row_select[2].button(':material/search:',key="search_btn")
        st.html("<style>.st-key-search_btn {position: absolute; top: 30px;}</style>")
        
        # df转换为字符串，按照search进行筛选
        df = df.astype(str)
        filtered_df = df[df[search_columns].str.contains(search, case=False)]
        
        # 增加一个多选框，用于选择要显示的列
        with row_select[3].popover("选择要显示的列"):
            select_columns = st.multiselect('选择要显示的列', df.columns, default=df.columns)
        st.html("<style>.stPopover {position: absolute; top: 25px;}</style>")
        filtered_df = filtered_df[select_columns]
        
        # show_add_delete = True
        limit = 10
        height = 402
        # if row_select[4].toggle("开关增删按钮"):
        #     show_add_delete = not show_add_delete
        #     display = "block" if show_add_delete else "none"
        #     limit = 10 if show_add_delete else 11
        #     height = 402 if show_add_delete else 452
        #     st.html("<style>.st-key-add_button {display: %s;}</style>" % (display))
        beijingtime = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
        row_select[5].download_button("⬇️导出下表数据", data=filtered_df.to_csv(index=False),
                                file_name=f"{beijingtime}data.csv", mime="text/csv")
        
        data_pages(df=filtered_df,limit=limit,height=height)

@st.fragment()
def style():
    st.html("""<style>
            /* 页顶的样式 */
            [data-testid="stHeader"] {
                height: 1px;
            }
            
            /* body主体的样式--边距 */
            .block-container { 
                padding: 20px 50px;
            }
            
            /* popover的样式--高度 */
            [data-testid="stPopoverBody"] {
                left : 30px;
                max-height: 700px;
                width: 500px;
            }
            /* 侧边栏的样式 */
            .stSidebar  {
                width: 250px;
            }
            /* 侧边栏的divider的样式--外边距 */
            div.st-emotion-cache-16txtl3.eczjsme4 > div > div > div > div > div:nth-child(6) > div > div > hr
            {margin-top: 0px;
            }

        </style>
        """)
    
@st.fragment()
def style2():
    st.html("""<style>
            .stButton > button {
            min-height: 100%;
            min-width: 100%;
            width: max-content;
                }
            .stDialog {
                top: -50px ;
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

# 主页面选择功能
def main():
    
    style2()
    # 数据库URL
    # 修改: 使用绝对路径确保数据库文件可以被正确访问
    database_name = "example.db"
    database_url = f"sqlite:///{database_name}"
    
    # 创建数据库引擎
    engine = create_database_engine(database_url)
    
    # 获取模型的属性名称、类型和默认值
    model_class = Data
    model_attributes, model_name = get_model_attributes(model_class)
    
    @st.dialog("数据操作", width="small")
    def dialog_operation(operation):
        if "新增" in operation:
            form_data, submit_button = generate_form_fields(model_attributes, model_name, button_label='提交')
            if submit_button:
                handle_add_submission(form_data, model_attributes, model_class, engine)
                st.html("<style>.stDialog {display: None;}</style>")           
                st.toast("数据已成功录入！")
                
                
        elif "修改" in operation:
            data_id = st.number_input("请输入数据ID", min_value=1, step=1)
            modify_data(data_id, model_attributes, model_class, engine)
            
        elif "查看" in operation:
            data_id = st.number_input("请输入数据ID", min_value=1, step=1)
            view_data_by_id(data_id, model_attributes, model_class, engine)
        elif "删除" in operation:
            data_id = st.number_input("请输入数据ID", min_value=1, step=1)
            delete_data_with_confirmation(data_id, model_attributes, model_class, engine)
            
        

    st.markdown("### 数据管理")
    # 添加四个按钮，分别对应“新增”、“修改”、“查看”、“删除”操作
    with st.container(key="add_button"):
        rows = st.columns([1, 1, 1, 1,10])
        if rows[0].button(":material/add:新增"):
            dialog_operation("新增")
        if rows[1].button(":material/edit:修改"):
            dialog_operation("修改")
        if rows[2].button(":material/search:查看"):
            dialog_operation("查看")
        if rows[3].button(":material/delete:删除", type="primary"):
            dialog_operation("删除")
    
    # 显示数据表格(含分页功能)
    display_data(model_class, engine)

if __name__ == "__main__":
    st.set_page_config(page_title="数据管理系统", page_icon=":material/database:", layout="wide")
    style()
    main()
    with st.sidebar:
        st.text("数据管理系统")
    
    

