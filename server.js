// Cloudflare Worker: Static Assets + HuggingFace Zero-CORS Stream Proxy
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // 处理 CORS 预检请求
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
          'Access-Control-Allow-Headers': '*',
        }
      });
    }

    // 模型反向代理：/model-proxy/:mirror/:path...
    if (url.pathname.startsWith('/model-proxy/')) {
      const match = url.pathname.match(/^\/model-proxy\/(china|global)\/(.*)$/);
      if (match) {
        const mirror = match[1];
        const subPath = match[2];
        const targetHost = mirror === 'china' ? 'https://hf-mirror.com' : 'https://huggingface.co';
        const targetUrl = `${targetHost}/${subPath}`;

        try {
          const resp = await fetch(targetUrl, {
            headers: {
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            redirect: 'follow'
          });

          const newHeaders = new Headers(resp.headers);
          newHeaders.set('Access-Control-Allow-Origin', '*');
          newHeaders.set('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
          newHeaders.set('Cross-Origin-Resource-Policy', 'cross-origin');

          return new Response(resp.body, {
            status: resp.status,
            headers: newHeaders
          });
        } catch (err) {
          return new Response(`Proxy error: ${err.message}`, { status: 502 });
        }
      }
    }

    // 默认静态资产服务
    if (env.ASSETS) {
      return env.ASSETS.fetch(request);
    }

    return new Response('Not Found', { status: 404 });
  }
};
