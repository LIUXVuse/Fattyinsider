// 这个文件只是为了确保Node.js构建器能够正常工作
// 实际的应用程序入口点是vercel_app.py

console.log('Node.js构建器已启动');
console.log('正在执行Python构建脚本...');

// 导出一个简单的函数，以便Vercel可以识别这是一个有效的Node.js模块
module.exports = (req, res) => {
  res.status(200).send('请访问主应用程序路径');
}; 