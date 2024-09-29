from typing import Optional

from sqlmodel import Field, SQLModel


class Company(SQLModel, table=True):

    @property
    def url(self):
        return f'https://www.qcc.com/firm/{self.id}.html'

    id: str = Field(primary_key=True)

    公司名称: str
    公司法人: str
    统一社会信用代码: str
    企业名称: str
    法定代表人: str
    登记状态: str
    注册资本: str
    成立日期: str
    实缴资本: str
    组织机构代码: str
    工商注册号: str
    纳税人识别号: str
    企业类型: str
    营业期限: str
    纳税人资质: str
    人员规模: str
    参保人数: str
    核准日期: str
    所属地区: str
    登记机关: str
    国标行业: str
    英文名: str
    注册地址: str
    经营范围: str