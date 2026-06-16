-- LeetCode 1978. 上级经理已离职的公司员工
-- 题目：找出薪水低于30000并且上级经理已经离职的员工ID
-- 思路：LEFT JOIN 自连接，找到 manager_id 在 Employees 表中找不到对应记录的员工

SELECT
    a.employee_id
FROM Employees a
LEFT JOIN Employees b
    ON a.manager_id = b.employee_id
WHERE a.salary < 30000
  AND a.manager_id IS NOT NULL
  AND b.employee_id IS NULL
ORDER BY a.employee_id;
