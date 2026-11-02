(function() {
	const m = new Uint32Array([
		1116352408,
		1899447441,
		3049323471,
		3921009573,
		961987163,
		1508970993,
		2453635748,
		2870763221,
		3624381080,
		310598401,
		607225278,
		1426881987,
		1925078388,
		2162078206,
		2614888103,
		3248222580,
		3835390401,
		4022224774,
		264347078,
		604807628,
		770255983,
		1249150122,
		1555081692,
		1996064986,
		2554220882,
		2821834349,
		2952996808,
		3210313671,
		3336571891,
		3584528711,
		113926993,
		338241895,
		666307205,
		773529912,
		1294757372,
		1396182291,
		1695183700,
		1986661051,
		2177026350,
		2456956037,
		2730485921,
		2820302411,
		3259730800,
		3345764771,
		3516065817,
		3600352804,
		4094571909,
		275423344,
		430227734,
		506948616,
		659060556,
		883997877,
		958139571,
		1322822218,
		1537002063,
		1747873779,
		1955562222,
		2024104815,
		2227730452,
		2361852424,
		2428436474,
		2756734187,
		3204031479,
		3329325298
	]), u = /* @__PURE__ */ new Uint32Array(64);
	function A(r) {
		if (typeof TextEncoder < "u") return new TextEncoder().encode(r);
		const o = [];
		for (let t = 0; t < r.length; t++) {
			const e = r.charCodeAt(t);
			e < 128 ? o.push(e) : e < 2048 ? o.push(192 | e >> 6, 128 | e & 63) : o.push(224 | e >> 12, 128 | e >> 6 & 63, 128 | e & 63);
		}
		return new Uint8Array(o);
	}
	function l(r, o) {
		return r >>> o | r << 32 - o;
	}
	function M(r, o, t) {
		for (let n = 0; n < 16; n++) {
			const i = o + n * 4;
			u[n] = (r[i] << 24 | r[i + 1] << 16 | r[i + 2] << 8 | r[i + 3]) >>> 0;
		}
		for (let n = 16; n < 64; n++) {
			const i = u[n - 15], w = u[n - 2], p = (l(i, 7) ^ l(i, 18) ^ i >>> 3) >>> 0, y = (l(w, 17) ^ l(w, 19) ^ w >>> 10) >>> 0;
			u[n] = u[n - 16] + p + u[n - 7] + y >>> 0;
		}
		let e = t[0], s = t[1], f = t[2], d = t[3], c = t[4], g = t[5], a = t[6], U = t[7];
		for (let n = 0; n < 64; n++) {
			const i = (l(c, 6) ^ l(c, 11) ^ l(c, 25)) >>> 0, w = (c & g ^ ~c & a) >>> 0, p = U + i + w + m[n] + u[n] >>> 0, y = ((l(e, 2) ^ l(e, 13) ^ l(e, 22)) >>> 0) + ((e & s ^ e & f ^ s & f) >>> 0) >>> 0;
			U = a, a = g, g = c, c = d + p >>> 0, d = f, f = s, s = e, e = p + y >>> 0;
		}
		t[0] = t[0] + e >>> 0, t[1] = t[1] + s >>> 0, t[2] = t[2] + f >>> 0, t[3] = t[3] + d >>> 0, t[4] = t[4] + c >>> 0, t[5] = t[5] + g >>> 0, t[6] = t[6] + a >>> 0, t[7] = t[7] + U >>> 0;
	}
	const x = "0123456789abcdef";
	function b(r) {
		const o = A(r), t = o.length * 8, e = new Uint8Array(o.length + 9 + 63 >> 6 << 6);
		e.set(o), e[o.length] = 128;
		const s = new DataView(e.buffer);
		s.setUint32(e.length - 8, Math.floor(t / 4294967296)), s.setUint32(e.length - 4, t >>> 0);
		const f = new Uint32Array([
			1779033703,
			3144134277,
			1013904242,
			2773480762,
			1359893119,
			2600822924,
			528734635,
			1541459225
		]);
		for (let c = 0; c < e.length; c += 64) M(e, c, f);
		let d = "";
		for (let c = 0; c < 8; c++) {
			const g = f[c];
			for (let a = 28; a >= 0; a -= 4) d += x[g >>> a & 15];
		}
		return d;
	}
	const v = 500;
	self.onmessage = (r) => {
		const { salt: o, challenge: t, max: e } = r.data;
		let s = 0;
		for (; s <= e;) {
			const f = Math.min(e, s + v - 1);
			for (; s <= f; s++) if (b(o + s) === t) {
				self.postMessage({
					type: "found",
					number: s
				});
				return;
			}
			self.postMessage({
				type: "progress",
				value: Math.min(1, s / (e + 1))
			});
		}
		self.postMessage({ type: "exhausted" });
	};
})();
