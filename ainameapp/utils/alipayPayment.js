import http from '@/http/http.js';

const DEFAULT_POLL_INTERVAL_MS = 2000;
const DEFAULT_TIMEOUT_MS = 15 * 60 * 1000;

export const startAlipayPayment = (payment, options = {}) => {
  const outTradeNo = payment?.out_trade_no || '';
  const paymentUrl = payment?.payment_url || '';
  const pendingKey = options.pendingKey || '';
  const paidRedirectUrl = options.paidRedirectUrl || (
    outTradeNo ? `/pages/payment/result?out_trade_no=${encodeURIComponent(outTradeNo)}&status=success` : ''
  );

  if (!paymentUrl) {
    uni.showToast({ title: '缺少支付宝支付链接', icon: 'none' });
    return;
  }
  if (pendingKey && outTradeNo) {
    uni.setStorageSync(pendingKey, outTradeNo);
  }

  // #ifdef H5
  const payWindow = options.payWindow || window.open('', '_blank');
  if (!payWindow) {
    window.location.href = paymentUrl;
    return;
  }
  payWindow.location.href = paymentUrl;
  uni.showToast({ title: '已打开支付宝支付页，支付成功后将自动同步', icon: 'none' });
  watchAlipayPayment(outTradeNo, { pendingKey, paidRedirectUrl, payWindow });
  // #endif

  // #ifndef H5
  uni.showToast({ title: '当前仅 H5 支持支付宝沙箱支付', icon: 'none' });
  // #endif
};

export const openAlipayWindow = () => {
  // #ifdef H5
  return window.open('', '_blank');
  // #endif
  // #ifndef H5
  return null;
  // #endif
};

const watchAlipayPayment = (outTradeNo, options) => {
  if (!outTradeNo) return;
  const startedAt = Date.now();
  const timer = setInterval(async () => {
    if (Date.now() - startedAt >= DEFAULT_TIMEOUT_MS) {
      clearInterval(timer);
      uni.showToast({ title: '订单仍未支付，可在15分钟内继续支付', icon: 'none' });
      return;
    }
    try {
      const result = await http.syncAlipayOrder(outTradeNo, { silent: true });
      if (result.status === 'PAID') {
        clearInterval(timer);
        if (options.pendingKey) uni.removeStorageSync(options.pendingKey);
        try { options.payWindow?.close?.(); } catch (e) {}
        if (options.paidRedirectUrl) {
          uni.reLaunch({ url: options.paidRedirectUrl });
        }
      } else if (['CANCELLED', 'REFUNDED'].includes(result.status)) {
        clearInterval(timer);
        if (options.pendingKey) uni.removeStorageSync(options.pendingKey);
      }
    } catch (e) {
      // Payment may not be visible to Alipay query yet; keep polling.
    }
  }, DEFAULT_POLL_INTERVAL_MS);
};
