import hashlib
import os
import sqlite3
import utils.globals as globals

'''
获取到触发429的token后
计算SHA1哈希值
删除token.txt文件对应的token
修改account表的at_hash字段为SHA1哈希值对应的at_wait_time和status为1
time时间格式：2025-02-09 02:29:08
'''


def load_tokens(filepath=globals.TOKENS_FILE):
    globals.token_list = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    globals.token_list.append(line.strip())
    else:
        with open(filepath, "w", encoding="utf-8") as f:  # 如果文件不存在，则创建一个空文件
            pass
    return globals.token_list


def token_write_file():
    with open(globals.TOKENS_FILE, "w", encoding="utf-8") as f:
        for token in globals.token_list:
            f.write(token + "\n")

    with open(globals.TOKENS_SHA1_FILE, "w", encoding="utf-8") as f:
        for sha1_hash in globals.token_sha1_list:
            f.write(sha1_hash + "\n")  # 每行一个哈希值
    print("update token and sha hashes written complete")


def generate_and_write_sha1():
    """
    遍历 token_list，计算每个 token 的 SHA1 哈希值，
    并将哈希值写入到 TOKENS_SHA1_FILE 文件中。

    Returns:
        None
    """
    globals.token_sha1_list = []
    for token in globals.token_list:
        # 计算 SHA1 哈希值
        sha1_hash = hashlib.sha1(token.encode('utf-8')).hexdigest()
        globals.token_sha1_list.append(sha1_hash)

    with open(globals.TOKENS_SHA1_FILE, "w", encoding="utf-8") as f:
        for sha1_hash in globals.token_sha1_list:
            f.write(sha1_hash + "\n")  # 每行一个哈希值

    print(f"SHA1 hashes written to: {globals.TOKENS_SHA1_FILE}")


def remove_token_by_at_hash(at_hash, token_list=globals.token_list, token_sha1_list=globals.token_sha1_list):
    """
    根据 at_hash 值删除 token 及其对应的 SHA1 哈希值。

    Args:
        at_hash: 要查找的 at_hash 值。
        token_list: 包含 token 的列表。
        token_sha1_list: 包含 token SHA1 哈希值的列表。

    Returns:
        如果找到并删除了 token，则返回 True；否则返回 False。
        返回更新后的token_list, token_sha1_list
    """
    try:
        index = token_sha1_list.index(at_hash)  # 查找 at_hash 的索引
        deleted_token = token_list.pop(index)  # 从 token_list 中删除 token
        token_sha1_list.pop(index)  # 从 token_sha1_list 中删除对应的哈希值
        print(f"Token '{deleted_token}' and its SHA1 hash removed.")
        return True, token_list, token_sha1_list
    except ValueError:
        print(f"No token found with at_hash: {at_hash}")
        return False, token_list, token_sha1_list


def update_account_by_at_hash(at_hash, at_wait_time, status=1):
    """
    根据 at_hash 更新 account 表中的 at_wait_time 和 status。

    Args:
        at_hash: 要查找的 at_hash 值。
        at_wait_time: 要更新的 at_wait_time 值 (默认为 "")。
        at_wait_time时间格式：2025-02-09 02:29:08
        status: 要更新的 status 值 (默认为 1)。

    Returns:
        如果更新成功，则返回 True；否则返回 False。
    """
    try:
        # 连接到数据库（如果文件不存在，会自动创建）
        conn = sqlite3.connect(globals.DATABASE_FILE)
        cursor = conn.cursor()

        # 执行更新语句
        cursor.execute(
            """
            UPDATE account
            SET at_wait_time = ?, status = ?
            WHERE at_hash = ?
            """,
            (at_wait_time, status, at_hash),
        )

        # 提交更改
        conn.commit()

        # 检查是否更新了任何行
        if cursor.rowcount > 0:
            print(f"Account with at_hash '{at_hash}' updated successfully.")
            ret = True
        else:
            print(f"No account found with at_hash: {at_hash}")
            ret = False
        return ret

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        # 关闭连接
        if conn:
            conn.close()


def dealAt429(at, time):
    at_hash = hashlib.sha1(at.encode('utf-8')).hexdigest()

    # 删除token.txt文件对应的token
    remove_token_by_at_hash(at_hash)

    # 将token和sha1写入到文件中
    token_write_file()

    # 修改account表的at_hash字段为SHA1哈希值对应的at_wait_time和status为1
    update_account_by_at_hash(at_hash=at_hash, at_wait_time=time, status=1)


# 初始加载
# globals.token_list = load_tokens()
