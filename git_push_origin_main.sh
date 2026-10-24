# git_push_origin_main.sh
# github.com/shenjuexiao
# 20261022


# 进入项目目录
# cd bing-uhd-simple

# GITEE
git remote set-url --delete origin git@gitee.com:bing-men/bing-uhd-simple.git
git remote set-url --add origin git@gitee.com:bing-men/bing-uhd-simple.git

# 暂存所有更改
git add .

# 提交更改
git commit -m "$(date +%Y%m%d)"

# 推送到远程 main 分支
git push origin main

# 提示完成
echo "✅ 执行完成！按任意键退出..."

# 等待任意键输入
read -n 1