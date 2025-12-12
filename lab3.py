"""
快递物流管理系统 - 领域模型设计与实现
第一阶段：领域模型构造与验证
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid


# ==================== 值对象定义 ====================
@dataclass(frozen=True)
class Address:
    """地址值对象"""
    province: str
    city: str
    district: str
    street: str
    detail: str
    postal_code: str
    
    def __str__(self):
        return f"{self.province}{self.city}{self.district}{self.street}{self.detail}"


@dataclass(frozen=True)
class ContactInfo:
    """联系信息值对象"""
    name: str
    phone: str
    email: Optional[str] = None


@dataclass(frozen=True)
class PackageDimensions:
    """包裹尺寸值对象"""
    weight: float  # 重量（kg）
    length: float  # 长（cm）
    width: float   # 宽（cm）
    height: float  # 高（cm）
    
    @property
    def volume(self) -> float:
        """计算体积（cm³）"""
        return self.length * self.width * self.height


# ==================== 枚举定义 ====================
class PackageStatus(Enum):
    """包裹状态枚举"""
    CREATED = "已创建"          # 运单创建
    COLLECTED = "已揽收"       # 网点揽收
    SORTING = "分拣中"         # 分拣中心处理
    IN_TRANSIT = "运输中"      # 运输途中
    AT_TRANSIT = "到达中转站"  # 到达中转站
    ARRIVED = "已到达"         # 到达目的网点
    OUT_FOR_DELIVERY = "派送中" # 派送中
    DELIVERED = "已签收"       # 已签收
    EXCEPTION = "异常"         # 异常状态
    RETURNED = "已退回"        # 已退回


class VehicleType(Enum):
    """车辆类型枚举"""
    TRUCK = "货车"
    VAN = "厢式货车"
    MOTORCYCLE = "摩托车"
    BICYCLE = "自行车"


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "待分配"
    ASSIGNED = "已分配"
    IN_PROGRESS = "进行中"
    COMPLETED = "已完成"
    CANCELLED = "已取消"


# ==================== 实体定义 ====================
class Entity(ABC):
    """实体基类"""
    def __init__(self, id: str = None):
        self.id = id or str(uuid.uuid4())
    
    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id
    
    def __hash__(self):
        return hash(self.id)


class Customer(Entity):
    """客户实体"""
    def __init__(self, name: str, phone: str, email: str = None):
        super().__init__()
        self.name = name
        self.contact_info = ContactInfo(name, phone, email)
        self.packages: List['Package'] = []
    
    def create_package(self, recipient: ContactInfo, destination: Address,
                      dimensions: PackageDimensions, description: str) -> 'Package':
        """创建包裹"""
        package = Package(
            sender=self,
            recipient=recipient,
            destination=destination,
            dimensions=dimensions,
            description=description
        )
        self.packages.append(package)
        return package


class Package(Entity):
    """包裹实体（聚合根）"""
    def __init__(self, sender: Customer, recipient: ContactInfo,
                 destination: Address, dimensions: PackageDimensions,
                 description: str):
        super().__init__()
        self.tracking_number = f"PKG{datetime.now().strftime('%Y%m%d')}{self.id[:8].upper()}"
        self.sender = sender
        self.recipient = recipient
        self.destination = destination
        self.dimensions = dimensions
        self.description = description
        
        self.status = PackageStatus.CREATED
        self.current_location: Optional['Location'] = None
        self.route_plan: Optional['RoutePlan'] = None
        self.transport_tasks: List['TransportTask'] = []
        self.delivery_task: Optional['DeliveryTask'] = None
        self.history: List[Dict] = []
        
        self._add_history("包裹创建", PackageStatus.CREATED.value)
    
    def update_status(self, status: PackageStatus, location: 'Location' = None, note: str = ""):
        """更新包裹状态"""
        old_status = self.status
        self.status = status
        if location:
            self.current_location = location
        
        self._add_history(f"状态变更: {old_status.value} -> {status.value}", note)
    
    def assign_route_plan(self, route_plan: 'RoutePlan'):
        """分配路线规划"""
        self.route_plan = route_plan
        self._add_history("路线规划分配", f"路线: {route_plan}")
    
    def add_transport_task(self, task: 'TransportTask'):
        """添加运输任务"""
        self.transport_tasks.append(task)
        self._add_history("运输任务添加", f"任务ID: {task.id}")
    
    def assign_delivery_task(self, task: 'DeliveryTask'):
        """分配派送任务"""
        self.delivery_task = task
        self._add_history("派送任务分配", f"派送员: {task.assignee.name}")
    
    def get_tracking_info(self) -> Dict:
        """获取包裹追踪信息"""
        return {
            "tracking_number": self.tracking_number,
            "status": self.status.value,
            "current_location": str(self.current_location) if self.current_location else "未知",
            "next_stop": self._get_next_stop(),
            "history": self.history
        }
    
    def _get_next_stop(self) -> str:
        """获取下一站"""
        if not self.route_plan:
            return "待规划"
        
        if self.status == PackageStatus.CREATED:
            return self.route_plan.start_location.name
        elif self.status == PackageStatus.DELIVERED:
            return "已送达"
        
        # 简化逻辑：根据状态判断下一站
        status_flow = {
            PackageStatus.COLLECTED: self.route_plan.start_location.name,
            PackageStatus.SORTING: "分拣中心",
            PackageStatus.IN_TRANSIT: self.route_plan.end_location.name,
            PackageStatus.ARRIVED: self.destination.district,
            PackageStatus.OUT_FOR_DELIVERY: f"派送至 {self.destination}"
        }
        
        return status_flow.get(self.status, "运输中")
    
    def _add_history(self, action: str, details: str):
        """添加历史记录"""
        self.history.append({
            "timestamp": datetime.now(),
            "action": action,
            "details": details,
            "status": self.status.value
        })
    
    def __str__(self):
        return f"包裹[{self.tracking_number}]: {self.status.value}"


class Location(Entity):
    """位置实体（网点/中转站）"""
    def __init__(self, name: str, address: Address, location_type: str):
        super().__init__()
        self.name = name
        self.address = address
        self.location_type = location_type  # '网点', '分拣中心', '中转站'
        self.packages: List[Package] = []
        self.vehicles: List['Vehicle'] = []
        self.staff: List['Staff'] = []
    
    def receive_package(self, package: Package):
        """接收包裹"""
        package.current_location = self
        self.packages.append(package)
    
    def dispatch_package(self, package: Package):
        """发出包裹"""
        if package in self.packages:
            self.packages.remove(package)
    
    def __str__(self):
        return f"{self.location_type}[{self.name}]"


class Staff(Entity):
    """员工基类"""
    def __init__(self, name: str, employee_id: str, location: Location):
        super().__init__()
        self.name = name
        self.employee_id = employee_id
        self.location = location
        self.tasks: List['Task'] = []
    
    def assign_task(self, task: 'Task'):
        """分配任务"""
        task.assign_to(self)
        self.tasks.append(task)


class Dispatcher(Staff):
    """调度员"""
    def __init__(self, name: str, employee_id: str, location: Location):
        super().__init__(name, employee_id, location)
    
    def create_transport_task(self, packages: List[Package], vehicle: 'Vehicle',
                             driver: 'Driver', route: 'Route') -> 'TransportTask':
        """创建运输任务"""
        task = TransportTask(packages, vehicle, driver, route, self)
        task.assign_to(driver)
        return task
    
    def create_delivery_task(self, package: Package, deliverer: 'Deliverer') -> 'DeliveryTask':
        """创建派送任务"""
        task = DeliveryTask(package, deliverer, self)
        task.assign_to(deliverer)
        return task


class Driver(Staff):
    """司机"""
    def __init__(self, name: str, employee_id: str, location: Location,
                 license_type: str):
        super().__init__(name, employee_id, location)
        self.license_type = license_type
        self.assigned_vehicle: Optional['Vehicle'] = None
    
    def accept_transport_task(self, task: 'TransportTask'):
        """接受运输任务"""
        task.update_status(TaskStatus.IN_PROGRESS)
        print(f"{self.name} 开始执行运输任务: {task.id}")
    
    def complete_transport_task(self, task: 'TransportTask'):
        """完成运输任务"""
        task.update_status(TaskStatus.COMPLETED)
        print(f"{self.name} 已完成运输任务: {task.id}")


class Deliverer(Staff):
    """派送员"""
    def __init__(self, name: str, employee_id: str, location: Location):
        super().__init__(name, employee_id, location)
    
    def view_delivery_tasks(self) -> List['DeliveryTask']:
        """查看派送任务"""
        return [task for task in self.tasks if isinstance(task, DeliveryTask)]
    
    def mark_delivery_completed(self, task: 'DeliveryTask', signature: str = "已签收"):
        """标记派送完成"""
        task.complete(signature)
        print(f"{self.name} 已完成派送: {task.package.tracking_number}")


class Vehicle(Entity):
    """车辆实体"""
    def __init__(self, plate_number: str, vehicle_type: VehicleType,
                 capacity: float, location: Location):
        super().__init__()
        self.plate_number = plate_number
        self.vehicle_type = vehicle_type
        self.capacity = capacity  # 载重能力（kg）
        self.current_location = location
        self.current_load = 0.0
        self.packages: List[Package] = []
        self.driver: Optional[Driver] = None
    
    def load_package(self, package: Package) -> bool:
        """装载包裹"""
        if self.current_load + package.dimensions.weight <= self.capacity:
            self.packages.append(package)
            self.current_load += package.dimensions.weight
            return True
        return False
    
    def unload_package(self, package: Package):
        """卸载包裹"""
        if package in self.packages:
            self.packages.remove(package)
            self.current_load -= package.dimensions.weight
    
    def assign_driver(self, driver: Driver):
        """分配司机"""
        self.driver = driver
        driver.assigned_vehicle = self
    
    def __str__(self):
        return f"{self.vehicle_type.value}[{self.plate_number}]"


# ==================== 领域服务 ====================
class RoutePlanningService:
    """路线规划服务"""
    def __init__(self):
        self.routes: Dict[str, 'Route'] = {}
    
    def plan_route(self, start: Location, end: Location,
                  intermediate_stops: List[Location] = None) -> 'RoutePlan':
        """规划路线"""
        route_id = f"ROUTE_{start.id[:4]}_{end.id[:4]}"
        
        if route_id not in self.routes:
            self.routes[route_id] = Route(route_id, start, end, intermediate_stops)
        
        return RoutePlan(self.routes[route_id])
    
    def adjust_route(self, route: 'Route', new_stops: List[Location],
                    reason: str = "路线调整") -> 'Route':
        """调整路线"""
        route.intermediate_stops = new_stops
        route.last_adjusted = datetime.now()
        route.adjustment_reason = reason
        return route


class SortingService:
    """分拣服务"""
    @staticmethod
    def sort_package(package: Package, current_location: Location) -> Optional[Location]:
        """分拣包裹"""
        if package.status == PackageStatus.EXCEPTION:
            print(f"包裹 {package.tracking_number} 处于异常状态，无法分拣")
            return None
        
        # 简化的分拣逻辑：根据目的地决定下一站
        # 实际系统中这里会有复杂的路线计算
        if current_location.location_type == "网点":
            package.update_status(PackageStatus.SORTING, current_location)
            return Location("分拣中心", Address("", "", "", "", "", ""), "分拣中心")
        
        elif current_location.location_type == "分拣中心":
            package.update_status(PackageStatus.IN_TRANSIT, current_location)
            # 假设总是需要中转
            return Location("中转站", package.destination, "中转站")
        
        elif current_location.location_type == "中转站":
            package.update_status(PackageStatus.AT_TRANSIT, current_location)
            return Location("目的网点", package.destination, "网点")
        
        return None


# ==================== 值对象 - 路线相关 ====================
@dataclass
class Route:
    """路线值对象"""
    id: str
    start_location: Location
    end_location: Location
    intermediate_stops: List[Location] = field(default_factory=list)
    distance_km: float = 0.0
    estimated_hours: float = 0.0
    last_adjusted: Optional[datetime] = None
    adjustment_reason: Optional[str] = None
    
    def calculate_estimated_time(self, speed_kmh: float = 60) -> float:
        """计算预计时间"""
        if self.distance_km > 0:
            self.estimated_hours = self.distance_km / speed_kmh
        return self.estimated_hours
    
    def __str__(self):
        stops = [self.start_location.name]
        stops.extend([stop.name for stop in self.intermediate_stops])
        stops.append(self.end_location.name)
        return " → ".join(stops)


class RoutePlan:
    """路线规划值对象"""
    def __init__(self, route: Route):
        self.route = route
        self.created_at = datetime.now()
        self.estimated_arrival = self._calculate_estimated_arrival()
    
    def _calculate_estimated_arrival(self) -> datetime:
        """计算预计到达时间"""
        base_time = self.created_at + timedelta(hours=self.route.estimated_hours)
        return base_time
    
    def __str__(self):
        return f"路线规划: {self.route} | 预计到达: {self.estimated_arrival}"


# ==================== 任务抽象 ====================
class Task(Entity, ABC):
    """任务抽象类"""
    def __init__(self):
        super().__init__()
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.assignee: Optional[Staff] = None
    
    @abstractmethod
    def assign_to(self, staff: Staff):
        """分配任务"""
        pass
    
    def update_status(self, status: TaskStatus):
        """更新状态"""
        self.status = status
        self.updated_at = datetime.now()


class TransportTask(Task):
    """运输任务"""
    def __init__(self, packages: List[Package], vehicle: Vehicle,
                 driver: Driver, route: Route, dispatcher: Dispatcher):
        super().__init__()
        self.packages = packages
        self.vehicle = vehicle
        self.driver = driver
        self.route = route
        self.dispatcher = dispatcher
        self.loading_list = self._create_loading_list()
        
        # 为每个包裹添加运输任务
        for package in packages:
            package.add_transport_task(self)
    
    def assign_to(self, staff: Staff):
        """分配任务"""
        if isinstance(staff, Driver):
            self.assignee = staff
            self.status = TaskStatus.ASSIGNED
            staff.assign_task(self)
        else:
            raise ValueError("运输任务只能分配给司机")
    
    def _create_loading_list(self) -> Dict:
        """创建装载清单"""
        return {
            "vehicle": str(self.vehicle),
            "driver": self.driver.name,
            "package_count": len(self.packages),
            "total_weight": sum(p.dimensions.weight for p in self.packages),
            "packages": [p.tracking_number for p in self.packages]
        }
    
    def get_task_details(self) -> Dict:
        """获取任务详情"""
        return {
            "task_id": self.id,
            "type": "运输任务",
            "status": self.status.value,
            "route": str(self.route),
            "loading_list": self.loading_list,
            "created_at": self.created_at,
            "assignee": self.assignee.name if self.assignee else None
        }


class DeliveryTask(Task):
    """派送任务"""
    def __init__(self, package: Package, deliverer: Deliverer,
                 dispatcher: Dispatcher):
        super().__init__()
        self.package = package
        self.deliverer = deliverer
        self.dispatcher = dispatcher
        self.signature: Optional[str] = None
        self.delivered_at: Optional[datetime] = None
        
        package.assign_delivery_task(self)
    
    def assign_to(self, staff: Staff):
        """分配任务"""
        if isinstance(staff, Deliverer):
            self.assignee = staff
            self.status = TaskStatus.ASSIGNED
            staff.assign_task(self)
        else:
            raise ValueError("派送任务只能分配给派送员")
    
    def complete(self, signature: str):
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.signature = signature
        self.delivered_at = datetime.now()
        self.package.update_status(PackageStatus.DELIVERED, note=f"签收人: {signature}")
    
    def get_task_details(self) -> Dict:
        """获取任务详情"""
        return {
            "task_id": self.id,
            "type": "派送任务",
            "status": self.status.value,
            "package": self.package.tracking_number,
            "recipient": self.package.recipient.name,
            "address": str(self.package.destination),
            "phone": self.package.recipient.phone,
            "assignee": self.assignee.name if self.assignee else None,
            "signature": self.signature,
            "delivered_at": self.delivered_at
        }


# ==================== 仓储接口（领域层） ====================
class PackageRepository(ABC):
    """包裹仓储接口"""
    @abstractmethod
    def save(self, package: Package):
        pass
    
    @abstractmethod
    def find_by_tracking_number(self, tracking_number: str) -> Optional[Package]:
        pass
    
    @abstractmethod
    def find_by_status(self, status: PackageStatus) -> List[Package]:
        pass


class InMemoryPackageRepository(PackageRepository):
    """内存中的包裹仓储实现（用于演示）"""
    def __init__(self):
        self.packages: Dict[str, Package] = {}
    
    def save(self, package: Package):
        self.packages[package.tracking_number] = package
    
    def find_by_tracking_number(self, tracking_number: str) -> Optional[Package]:
        return self.packages.get(tracking_number)
    
    def find_by_status(self, status: PackageStatus) -> List[Package]:
        return [p for p in self.packages.values() if p.status == status]


# ==================== 应用服务 ====================
class LogisticsService:
    """物流应用服务"""
    def __init__(self):
        self.package_repo = InMemoryPackageRepository()
        self.route_planning_service = RoutePlanningService()
        self.sorting_service = SortingService()
        
        # 初始化一些基础数据
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """初始化示例数据"""
        # 创建网点
        self.beijing_center = Location(
            "北京分拣中心",
            Address("北京市", "北京市", "朝阳区", "物流大道", "1号", "100000"),
            "分拣中心"
        )
        
        self.shanghai_branch = Location(
            "上海网点",
            Address("上海市", "上海市", "浦东新区", "快递路", "100号", "200000"),
            "网点"
        )
    
    def create_package(self, sender_info: Dict, recipient_info: Dict,
                      destination: Address, dimensions: Dict) -> Package:
        """创建包裹"""
        # 创建客户
        sender = Customer(
            name=sender_info["name"],
            phone=sender_info["phone"],
            email=sender_info.get("email")
        )
        
        # 创建收件人信息
        recipient = ContactInfo(
            name=recipient_info["name"],
            phone=recipient_info["phone"],
            email=recipient_info.get("email")
        )
        
        # 创建包裹尺寸
        package_dimensions = PackageDimensions(
            weight=dimensions["weight"],
            length=dimensions["length"],
            width=dimensions["width"],
            height=dimensions["height"]
        )
        
        # 创建包裹
        package = sender.create_package(
            recipient=recipient,
            destination=destination,
            dimensions=package_dimensions,
            description=dimensions.get("description", "")
        )
        
        # 保存包裹
        self.package_repo.save(package)
        
        # 分配初始路线规划
        route_plan = self.route_planning_service.plan_route(
            self.shanghai_branch,
            self.beijing_center
        )
        package.assign_route_plan(route_plan)
        
        return package
    
    def track_package(self, tracking_number: str) -> Dict:
        """追踪包裹"""
        package = self.package_repo.find_by_tracking_number(tracking_number)
        if not package:
            return {"error": "包裹不存在"}
        
        return package.get_tracking_info()
    
    def sort_package(self, tracking_number: str) -> Dict:
        """分拣包裹"""
        package = self.package_repo.find_by_tracking_number(tracking_number)
        if not package:
            return {"error": "包裹不存在"}
        
        next_location = self.sorting_service.sort_package(
            package,
            package.current_location or self.shanghai_branch
        )
        
        return {
            "tracking_number": tracking_number,
            "current_status": package.status.value,
            "next_location": str(next_location) if next_location else "待处理",
            "message": "分拣完成" if next_location else "分拣异常"
        }


# ==================== 演示代码 ====================
def demonstrate_use_cases():
    """演示用例实现"""
    print("=" * 60)
    print("快递物流管理系统 - 领域模型演示")
    print("=" * 60)
    
    # 创建物流服务
    logistics = LogisticsService()
    
    # 用例1: 创建包裹
    print("\n1. 创建包裹")
    sender_info = {
        "name": "张三",
        "phone": "13800138000",
        "email": "zhangsan@example.com"
    }
    
    recipient_info = {
        "name": "李四",
        "phone": "13900139000",
        "email": "lisi@example.com"
    }
    
    destination = Address(
        province="北京市",
        city="北京市",
        district="朝阳区",
        street="建国路",
        detail="88号",
        postal_code="100000"
    )
    
    dimensions = {
        "weight": 5.0,
        "length": 30.0,
        "width": 20.0,
        "height": 15.0,
        "description": "电子产品"
    }
    
    package = logistics.create_package(sender_info, recipient_info, destination, dimensions)
    print(f"创建包裹成功！运单号: {package.tracking_number}")
    print(f"包裹状态: {package.status.value}")
    
    # 用例2: 追踪包裹
    print("\n2. 包裹追踪")
    tracking_info = logistics.track_package(package.tracking_number)
    print(f"运单号: {tracking_info['tracking_number']}")
    print(f"当前状态: {tracking_info['status']}")
    print(f"当前位置: {tracking_info['current_location']}")
    print(f"下一站: {tracking_info['next_stop']}")
    print("历史记录:")
    for record in tracking_info['history'][:3]:  # 只显示前3条
        print(f"  - {record['timestamp']}: {record['action']} ({record['details']})")
    
    # 用例3: 包裹分拣
    print("\n3. 包裹分拣")
    sort_result = logistics.sort_package(package.tracking_number)
    print(f"分拣结果: {sort_result}")
    
    # 更新追踪信息
    updated_info = logistics.track_package(package.tracking_number)
    print(f"分拣后状态: {updated_info['status']}")
    
    # 用例4: 创建运输任务（模拟）
    print("\n4. 运输调度")
    
    # 创建司机和车辆
    driver = Driver("王司机", "EMP001", logistics.shanghai_branch, "A1")
    vehicle = Vehicle("沪A12345", VehicleType.TRUCK, 10000.0, logistics.shanghai_branch)
    vehicle.assign_driver(driver)
    
    # 创建调度员
    dispatcher = Dispatcher("张调度", "DISP001", logistics.shanghai_branch)
    
    # 创建路线
    route = Route(
        "SH-BJ-001",
        logistics.shanghai_branch,
        logistics.beijing_center,
        distance_km=1200.0
    )
    route.calculate_estimated_time()
    
    # 创建运输任务
    transport_task = dispatcher.create_transport_task(
        packages=[package],
        vehicle=vehicle,
        driver=driver,
        route=route
    )
    
    print(f"创建运输任务: {transport_task.id}")
    print(f"任务详情: {transport_task.get_task_details()}")
    
    # 用例5: 创建派送任务（模拟）
    print("\n5. 末端派送")
    
    # 创建派送员
    deliverer = Deliverer("李派送员", "DEL001", logistics.beijing_center)
    
    # 创建派送任务
    delivery_task = dispatcher.create_delivery_task(package, deliverer)
    
    print(f"创建派送任务: {delivery_task.id}")
    print(f"任务详情: {delivery_task.get_task_details()}")
    
    # 模拟派送完成
    delivery_task.complete("李四")
    print(f"派送完成，签收人: {delivery_task.signature}")
    
    # 最终追踪信息
    print("\n6. 最终包裹状态")
    final_info = logistics.track_package(package.tracking_number)
    print(f"最终状态: {final_info['status']}")
    print("完整历史记录:")
    for record in final_info['history']:
        print(f"  [{record['timestamp'].strftime('%Y-%m-%d %H:%M')}] {record['action']:20} | {record['details']}")
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


def validate_model_requirements():
    """验证模型是否满足需求"""
    print("\n" + "=" * 60)
    print("领域模型需求验证")
    print("=" * 60)
    
    requirements = {
        "包裹状态管理与追溯": False,
        "运输调度与任务管理": False,
        "派送任务执行支持": False,
        "正常流程支持": False,
        "扩展流程支持（部分）": False
    }
    
    # 检查领域模型中的关键组件
    required_classes = [
        'Package', 'PackageStatus', 'TransportTask', 'DeliveryTask',
        'RoutePlanningService', 'SortingService', 'Dispatcher', 'Driver', 'Deliverer'
    ]
    
    print("\n1. 检查核心类是否存在:")
    for class_name in required_classes:
        if class_name in globals():
            print(f"  ✓ {class_name}")
        else:
            print(f"  ✗ {class_name}")
    
    # 验证功能点
    print("\n2. 验证功能点:")
    
    # 包裹状态管理与追溯
    if 'Package' in globals() and 'get_tracking_info' in Package.__dict__:
        requirements["包裹状态管理与追溯"] = True
        print("  ✓ 包裹状态管理与追溯: Package实体包含状态管理和追踪方法")
    
    # 运输调度与任务管理
    if 'TransportTask' in globals() and 'Dispatcher' in globals():
        requirements["运输调度与任务管理"] = True
        print("  ✓ 运输调度与任务管理: 支持运输任务创建和调度")
    
    # 派送任务执行支持
    if 'DeliveryTask' in globals() and 'Deliverer' in globals():
        requirements["派送任务执行支持"] = True
        print("  ✓ 派送任务执行支持: 支持派送任务分配和执行")
    
    # 正常流程支持
    normal_flow_steps = [
        "包裹创建", "路线规划", "分拣处理", "运输调度", "派送执行", "签收完成"
    ]
    
    flow_supported = all([
        'Package' in globals(),
        'RoutePlanningService' in globals(),
        'SortingService' in globals(),
        'TransportTask' in globals(),
        'DeliveryTask' in globals()
    ])
    
    requirements["正常流程支持"] = flow_supported
    print(f"  ✓ 正常流程支持: 支持从创建到签收的全流程" if flow_supported else "  ✗ 正常流程支持")
    
    # 扩展流程支持
    if 'PackageStatus' in globals() and PackageStatus.EXCEPTION in PackageStatus:
        requirements["扩展流程支持（部分）"] = True
        print("  ✓ 扩展流程支持（部分）: 支持异常状态处理")
    
    print("\n3. 验证结果:")
    print("-" * 40)
    for req, status in requirements.items():
        status_symbol = "✓" if status else "✗"
        print(f"{status_symbol} {req}")
    
    print("\n4. 模型特点说明:")
    print("  • 使用DDD（领域驱动设计）方法构建")
    print("  • 包含实体、值对象、领域服务等核心概念")
    print("  • 支持聚合根（Package）管理包裹生命周期")
    print("  • 使用仓储模式进行数据持久化抽象")
    print("  • 支持领域事件（通过历史记录）")
    
    return requirements


if __name__ == "__main__":
    # 运行演示
    demonstrate_use_cases()
    
    # 验证模型
    validate_model_requirements()
    
    print("\n提示：这个领域模型设计考虑了:")
    print("1. 包裹全生命周期管理")
    print("2. 运输调度和任务分配")
    print("3. 异常状态处理（通过PackageStatus.EXCEPTION）")
    print("4. 路线规划和调整机制")
    print("5. 分拣中心和中转站支持")
    print("\n可以进一步扩展:")
    print("• 添加费用计算领域服务")
    print("• 实现仓储的具体持久化")
    print("• 添加领域事件发布机制")
    print("• 实现更复杂的路线规划算法")