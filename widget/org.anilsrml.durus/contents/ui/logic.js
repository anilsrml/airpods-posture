// Servis durumu → widget görünümü. QML ve node testleri ortak kullanır.

var GRAY = "#95a5a6";

var STATES = {
    upright: { color: "#2ecc71", label: "Dik" },
    leaning: { color: "#f1c40f", label: "Eğik" },
    slouched: { color: "#e74c3c", label: "Kambur" },
    calibrating: { color: GRAY, label: "Sıfırlanıyor, dik dur" },
    disconnected: { color: GRAY, label: "AirPods bağlı değil" },
    paused: { color: GRAY, label: "Duraklatıldı" }
};

// s: GET /state yanıtı ya da servis yanıt vermiyorsa null.
function view(s) {
    var base = s ? STATES[s.state] : null;
    if (!base) {
        return { color: GRAY, label: "Servis çalışmıyor", detail: "" };
    }
    var detail = "";
    if (s.pitch !== null && s.pitch !== undefined) {
        detail = "Öne eğim: " + (s.pitch >= 0 ? "+" : "") + s.pitch.toFixed(1) + "°";
    }
    return { color: base.color, label: base.label, detail: detail };
}
