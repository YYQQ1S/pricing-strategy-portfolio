-- LeetCode 1341. 电影评分
-- 题目：找出评分数量最多的用户 + 2020年2月平均评分最高的电影
-- 结果用 UNION ALL 合并

-- ============================================================
-- 解法一：ORDER BY + LIMIT 1（简洁直观）
-- ============================================================
-- (
--     SELECT u.name AS results
--     FROM Users u
--     LEFT JOIN MovieRating mr ON u.user_id = mr.user_id
--     GROUP BY u.user_id
--     ORDER BY COUNT(*) DESC, name ASC
--     LIMIT 1
-- )
-- UNION ALL
-- (
--     SELECT m.title AS results
--     FROM Movies m
--     LEFT JOIN MovieRating mr ON m.movie_id = mr.movie_id
--     WHERE mr.created_at BETWEEN '2020-02-01' AND '2020-02-29'
--     GROUP BY m.movie_id
--     ORDER BY AVG(mr.rating) DESC, title ASC
--     LIMIT 1
-- );

-- ============================================================
-- 解法二：RANK() 窗口函数（更通用，可处理并列第一）
-- ============================================================
(SELECT
    name AS results
FROM (
    SELECT
        name,
        COUNT(movie_id) AS cnt,
        RANK() OVER (ORDER BY COUNT(movie_id) DESC, name ASC) AS ranking
    FROM Users a
    LEFT JOIN MovieRating b ON a.user_id = b.user_id
    GROUP BY a.user_id
) t
WHERE ranking = 1
)

UNION ALL

(SELECT
    title AS results
FROM (
    SELECT
        title,
        AVG(rating) AS avg_rating,
        RANK() OVER (ORDER BY AVG(rating) DESC, title ASC) AS ranking
    FROM Movies a
    LEFT JOIN MovieRating b ON a.movie_id = b.movie_id
    WHERE b.created_at BETWEEN '2020-02-01' AND '2020-02-29'
    GROUP BY a.movie_id
) t
WHERE ranking = 1
);
