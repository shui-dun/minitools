import const
import time
import subprocess

def wait_for_network():
    """等待网络连接可用"""
    url = const.NETWORK_TEST_URL
    while True:
        # curl 无视证书错误
        try:
            result = subprocess.run(
                ['curl', '-k', '-s', '-o', '/dev/null', '-w', '%{http_code}', url],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout.strip() == '200':
                break
            print("网络不可用，等待5秒后重试...")
        except Exception:
            print("网络连接异常，等待5秒后重试...")
            time.sleep(5)
        
if __name__ == "__main__":
    wait_for_network()
    print("网络已连接，继续执行后续操作")