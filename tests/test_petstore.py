"""
宠物商店 API 自动化测试
基于 Swagger 文档生成的 pytest 测试用例
"""
import pytest
import requests
import json


class TestPetStoreAPI:
    """宠物商店 API 测试类"""
    
    BASE_URL = "https://petstore3.swagger.io/api/v3"
    
    # 测试数据
    VALID_PET_DATA = {
        "id": 12345,
        "name": "测试宠物",
        "status": "available",
        "photoUrls": ["https://example.com/photo1.jpg"]
    }
    
    UPDATE_PET_DATA = {
        "id": 12345,
        "name": "更新后的宠物",
        "status": "sold",
        "photoUrls": ["https://example.com/photo2.jpg"]
    }

    def test_get_pet_by_id_success(self):
        """测试根据 ID 查询宠物 - 正常情况"""
        # 首先创建一个宠物用于查询
        requests.post(f"{self.BASE_URL}/pet", json=self.VALID_PET_DATA)
        
        # 查询宠物
        pet_id = self.VALID_PET_DATA["id"]
        response = requests.get(f"{self.BASE_URL}/pet/{pet_id}")
        
        # 断言
        assert response.status_code == 200
        pet_data = response.json()
        assert pet_data["id"] == pet_id
        assert pet_data["name"] == self.VALID_PET_DATA["name"]
        assert "photoUrls" in pet_data

    def test_get_pet_by_id_not_found(self):
        """测试根据 ID 查询宠物 - 宠物不存在"""
        non_existent_id = 999999
        response = requests.get(f"{self.BASE_URL}/pet/{non_existent_id}")
        
        # 断言
        assert response.status_code == 404

    def test_get_pet_by_id_invalid_parameter(self):
        """测试根据 ID 查询宠物 - 无效参数"""
        invalid_id = "invalid_id"
        response = requests.get(f"{self.BASE_URL}/pet/{invalid_id}")
        
        # 断言 - 期望返回错误状态码
        assert response.status_code in [400, 404]

    def test_add_pet_success(self):
        """测试添加新宠物 - 正常情况"""
        response = requests.post(f"{self.BASE_URL}/pet", json=self.VALID_PET_DATA)
        
        # 断言
        assert response.status_code == 200

    def test_add_pet_missing_required_field(self):
        """测试添加新宠物 - 缺少必填字段"""
        invalid_data = {
            "id": 12346,
            "status": "available"
            # 缺少必填字段 name 和 photoUrls
        }
        
        response = requests.post(f"{self.BASE_URL}/pet", json=invalid_data)
        
        # 断言
        assert response.status_code == 400

    def test_add_pet_invalid_status(self):
        """测试添加新宠物 - 无效状态值"""
        invalid_data = {
            "id": 12347,
            "name": "测试宠物",
            "status": "invalid_status",  # 无效的状态值
            "photoUrls": ["https://example.com/photo.jpg"]
        }
        
        response = requests.post(f"{self.BASE_URL}/pet", json=invalid_data)
        
        # 断言 - 某些实现可能接受无效状态，所以检查是否至少不是服务器错误
        assert response.status_code < 500

    def test_add_pet_empty_body(self):
        """测试添加新宠物 - 空请求体"""
        response = requests.post(f"{self.BASE_URL}/pet", json={})
        
        # 断言
        assert response.status_code == 400

    def test_update_pet_success(self):
        """测试更新宠物信息 - 正常情况"""
        # 首先创建一个宠物
        requests.post(f"{self.BASE_URL}/pet", json=self.VALID_PET_DATA)
        
        # 更新宠物信息
        response = requests.put(f"{self.BASE_URL}/pet", json=self.UPDATE_PET_DATA)
        
        # 断言
        assert response.status_code == 200

    def test_update_pet_not_found(self):
        """测试更新宠物信息 - 宠物不存在"""
        non_existent_pet_data = {
            "id": 999998,
            "name": "不存在的宠物",
            "status": "available",
            "photoUrls": ["https://example.com/photo.jpg"]
        }
        
        response = requests.put(f"{self.BASE_URL}/pet", json=non_existent_pet_data)
        
        # 断言
        assert response.status_code == 404

    def test_update_pet_missing_required_field(self):
        """测试更新宠物信息 - 缺少必填字段"""
        invalid_data = {
            "id": 12345,
            "status": "sold"
            # 缺少必填字段 name 和 photoUrls
        }
        
        response = requests.put(f"{self.BASE_URL}/pet", json=invalid_data)
        
        # 断言
        assert response.status_code == 400

    def test_find_pets_by_status_available(self):
        """测试根据状态查询宠物 - available状态"""
        # 确保有 available 状态的宠物
        available_pet = {
            "id": 12348,
            "name": "可购买宠物",
            "status": "available",
            "photoUrls": ["https://example.com/available.jpg"]
        }
        requests.post(f"{self.BASE_URL}/pet", json=available_pet)
        
        response = requests.get(f"{self.BASE_URL}/pet/findByStatus", 
                              params={"status": "available"})
        
        # 断言
        assert response.status_code == 200
        pets = response.json()
        assert isinstance(pets, list)
        # 检查返回的宠物都是 available 状态
        for pet in pets:
            if "status" in pet:
                assert pet["status"] == "available"

    def test_find_pets_by_status_pending(self):
        """测试根据状态查询宠物 - pending状态"""
        response = requests.get(f"{self.BASE_URL}/pet/findByStatus", 
                              params={"status": "pending"})
        
        # 断言
        assert response.status_code == 200
        pets = response.json()
        assert isinstance(pets, list)

    def test_find_pets_by_status_sold(self):
        """测试根据状态查询宠物 - sold状态"""
        response = requests.get(f"{self.BASE_URL}/pet/findByStatus", 
                              params={"status": "sold"})
        
        # 断言
        assert response.status_code == 200
        pets = response.json()
        assert isinstance(pets, list)

    def test_find_pets_by_status_invalid(self):
        """测试根据状态查询宠物 - 无效状态"""
        response = requests.get(f"{self.BASE_URL}/pet/findByStatus", 
                              params={"status": "invalid_status"})
        
        # 断言 - 期望返回错误状态码
        assert response.status_code in [400, 422]

    def test_find_pets_by_status_missing_parameter(self):
        """测试根据状态查询宠物 - 缺少必需参数"""
        response = requests.get(f"{self.BASE_URL}/pet/findByStatus")
        
        # 断言
        assert response.status_code == 400

    @pytest.mark.parametrize("status", ["available", "pending", "sold"])
    def test_find_pets_by_status_all_valid_statuses(self, status):
        """参数化测试：测试所有有效的宠物状态"""
        response = requests.get(f"{self.BASE_URL}/pet/findByStatus", 
                              params={"status": status})
        
        # 断言
        assert response.status_code == 200
        pets = response.json()
        assert isinstance(pets, list)

    def test_api_response_headers(self):
        """测试 API 响应头"""
        response = requests.get(f"{self.BASE_URL}/pet/findByStatus", 
                              params={"status": "available"})
        
        # 断言
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    def test_api_response_time(self):
        """测试 API 响应时间"""
        import time
        start_time = time.time()
        
        response = requests.get(f"{self.BASE_URL}/pet/findByStatus", 
                              params={"status": "available"})
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # 断言响应时间少于 5 秒
        assert response_time < 5.0
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])