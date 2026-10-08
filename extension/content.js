// Content script for VideoHunter (影速獵手)
let lastTargetUrl = null;

function findBestVideoUrl(target) {
  if (!target) return null;

  // 1. If clicked on or inside a video element with a direct playable stream (non-blob)
  let videoEl = target.tagName === 'VIDEO' ? target : target.querySelector('video') || target.closest('video');
  if (!videoEl) {
    const container = target.closest('article') || target.closest('div[role="dialog"]') || target.closest('div[role="article"]');
    if (container) videoEl = container.querySelector('video');
  }
  if (videoEl) {
    const src = videoEl.currentSrc || videoEl.src;
    if (src && !src.startsWith('blob:') && !src.startsWith('data:') && (src.includes('.mp4') || src.includes('cdninstagram') || src.includes('fbcdn'))) {
      return src;
    }
  }

  // 2. Check if clicked directly on a relevant link
  const directLink = target.closest('a');
  if (directLink && directLink.href) {
    const h = directLink.href;
    if (h.includes('/post/') || h.includes('/reel/') || h.includes('/p/') || 
        h.includes('/watch') || h.includes('/videos/') || h.includes('/shorts/') || 
        h.includes('/video/') || h.includes('/status/')) {
      return h;
    }
  }

  // 3. Threads post container / card
  const threadsCard = target.closest('article') || target.closest('div[role="article"]') || target.closest('div[data-pressable-container="true"]');
  if (threadsCard) {
    const postLink = threadsCard.querySelector('a[href*="/post/"]');
    if (postLink && postLink.href) return postLink.href;
  }

  // 4. Instagram card
  const igCard = target.closest('article') || target.closest('div[role="dialog"]');
  if (igCard) {
    const igLink = igCard.querySelector('a[href*="/reel/"]') || igCard.querySelector('a[href*="/p/"]');
    if (igLink && igLink.href) return igLink.href;
  }

  // 4. Facebook card
  const fbCard = target.closest('div[role="article"]') || target.closest('div[data-pagelet*="FeedUnit"]') || target.closest('div[data-pagelet*="Reel"]');
  if (fbCard) {
    const fbLink = fbCard.querySelector('a[href*="/reel/"]') || fbCard.querySelector('a[href*="/watch"]') || fbCard.querySelector('a[href*="/videos/"]');
    if (fbLink && fbLink.href) return fbLink.href;
  }

  // 5. Twitter / X card
  const tweetCard = target.closest('article');
  if (tweetCard) {
    const twLink = tweetCard.querySelector('a[href*="/status/"]');
    if (twLink && twLink.href) return twLink.href;
  }

  // 6. YouTube card
  const ytCard = target.closest('ytd-rich-item-renderer') || target.closest('ytd-video-renderer') || target.closest('ytd-reel-item-renderer');
  if (ytCard) {
    const ytLink = ytCard.querySelector('a#thumbnail') || ytCard.querySelector('a[href*="/watch"]') || ytCard.querySelector('a[href*="/shorts/"]');
    if (ytLink && ytLink.href) return ytLink.href;
  }

  // 7. Walk up the DOM tree looking for social video links
  let curr = target;
  for (let i = 0; i < 8 && curr; i++) {
    const a = curr.querySelector('a[href*="/post/"], a[href*="/reel/"], a[href*="/watch"], a[href*="/videos/"], a[href*="/video/"], a[href*="/status/"], a[href*="/shorts/"]');
    if (a && a.href) return a.href;
    curr = curr.parentElement;
  }

  // 8. Video element fallback
  if (videoEl) {
    const src = videoEl.currentSrc || videoEl.src;
    if (src && !src.startsWith('blob:') && !src.startsWith('data:')) {
      return src;
    }
  }

  // 9. Fallback to any closest anchor
  if (directLink && directLink.href && directLink.href.startsWith('http')) {
    return directLink.href;
  }

  return null;
}

document.addEventListener('contextmenu', (event) => {
  lastTargetUrl = findBestVideoUrl(event.target);
}, true);

// Listen for query from background service worker
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getVideoUrl') {
    sendResponse({ url: lastTargetUrl });
  }
  return true;
});
