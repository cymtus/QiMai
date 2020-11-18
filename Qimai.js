///////////////////////e.from//////////////////////////////////
// s函数的实现逻辑 可推断e.from 最后执行 d(t, e, n)
// function s(t, e, n, i) {
//     if ("number" == typeof e)
//         throw new TypeError('"value" argument must not be a number');
//     return "undefined" != typeof ArrayBuffer && e instanceof ArrayBuffer ? f(t, e, n, i) : "string" == typeof e ? d(t, e, n) : p(t, e)
// }
// a.from = function (t, e, n) {
//     return s(null, t, e, n)
// }

function G(t) {
    for (var e = [], n = 0; n < t.length; ++n)
        e.push(255 & t.charCodeAt(n));
    return e
}

//
function X(t, e, n, i) {
    for (var r = 0; r < i && !(r + n >= e.length || r >= t.length); ++r)
        e[r + n] = t[r];
    return r
}

//
function t_write(t, e, n, i) {
    return X(G(e), t, n, i)
}

function o(t, e) {
    t = new Uint8Array(e)
    return t
}

// d(t, e, n)实现逻辑
function d(t, e, n) {
    // console.info(t, e, n)
    // var i = 0 | m(e, n);根据参数n，返回e的length
    var i = 0 | e.length;
    t = o(t, i);
    var e_in_k = 0
    var r = t_write(t, e, e_in_k, i);

    return t = t.slice(0, r), t
}


///////////////////////n.toString("base64")//////////////////////////////////
// a.prototype.toString = function() {
//     var t = 0 | this.length;
//     return 0 === t ? "" : 0 === arguments.length ? O(this, 0, t) : y.apply(this, arguments)
// }

// 执行y.apply
// function k(t, e, n) {
//0 === e && n === t.length
// true
// return 0 === e && n === t.length ? Z.fromByteArray(t) : Z.fromByteArray(t.slice(e, n))
// }
u = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "+", "/"]

function a(t) {
    return u[t >> 18 & 63] + u[t >> 12 & 63] + u[t >> 6 & 63] + u[63 & t]
}

//  o.push(s(t, l, l + a > c ? c : l + a));
function s(t, e, n) {
    for (var i, r = [], o = e; o < n; o += 3)
        i = (t[o] << 16 & 16711680) + (t[o + 1] << 8 & 65280) + (255 & t[o + 2]),
            r.push(a(i));
    return r.join("")
}

// Z.fromByteArray
function l(t) {
    for (var e, n = t.length, i = n % 3, r = "", o = [], a = 16383, l = 0, c = n - i; l < c; l += a)
        o.push(s(t, l, l + a > c ? c : l + a));
    return 1 === i ? (e = t[n - 1],
        r += u[e >> 2],
        r += u[e << 4 & 63],
        r += "==") : 2 === i && (e = (t[n - 2] << 8) + t[n - 1],
        r += u[e >> 10],
        r += u[e >> 4 & 63],
        r += u[e << 2 & 63],
        r += "="),
        o.push(r),
        o.join("")
}

///////////////////////U()函数/////////////////////////////////
// U() 三目运算符，自己判断执行逻辑 子函数 e.from / n.toString("base64")
// instanceof运算符用于测试构造函数的prototype属性是否出现在对象的原型链中的任何位置
function n_(t) {
    var n;
    return n = d(null, t.toString(), "binary"), l(n)
    // return n = t instanceof e ? t : e.from(t.toString(), "binary"),
    //     n.toString("base64")
}

///////////////////////f[Oa]函数/////////////////////////////////
function m(n) {
    return String["fromCharCode"](n)
}

function v(n) {
    return n_(encodeURIComponent(n)["replace"](/%([0-9A-F]{2})/g, function (a, n) {
        return m("0x" + n)
    }))
}

///////////////////////f[aL]函数/////////////////////////////////
function k(a, n) {
    a = a.split("")
    for (var t = a.length, e = n.length, r = "charCodeAt", i = 0; i < t; i++)
        a[i] = m(a[i][r](0) ^ n[(i + 10) % e][r](0));
    return a.join("")
}

// 混淆代码
// function k(a, n) {
//     n || (n = s()),
//         a = a[z](w);
//     for (var t = a[$s], e = n[$s], r = zh, i = h; i < t; i++)
//         a[i] = m(a[i][r](h) ^ n[(i + Up) % e][r](h));
//     return a[G](w)
// }

///////////////////////debug/////////////////////////////////
// var e = 49710072283;
// var m_str = "MTQyMDE5LTA4LTAzNg==@#/rank/marketRank@#49710072283@#1";
// var b_str = "00000008d78d46a";
// var analysis = v(k(m_str, b_str));
// console.info(analysis)

//dTB5Tyx0dQV8ZHEEdDB2QipTC1xwEx9CUV5bFwlWSg9RQjNRXltwEwQJD10EClIABFgHcBMB

// b是固定值，m生成方式
function get_analysis(m,b){
    var analysis = v(k(m, b));
    return analysis
}
