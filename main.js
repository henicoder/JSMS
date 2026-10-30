/* =========================================
   LUMIÈRE JEWELS - DATABASE CART
   ========================================= */

/*
   This cart uses the Flask/MySQL database cart.
   It does NOT use localStorage.

   Flow:
   User -> Customer -> Cart -> CartItem -> Product
*/


/* =========================================
   CSRF TOKEN
   ========================================= */

function getCsrfToken() {
    const meta = document.querySelector(
        'meta[name="csrf-token"]'
    );

    return meta
        ? meta.getAttribute("content")
        : "";
}


/* =========================================
   ADD TO CART
   ========================================= */

async function addToCart(productId) {

    try {

        const csrfToken = getCsrfToken();

        const response = await fetch(
            `/products/api/${productId}/add-to-cart`,
            {
                method: "POST",

                credentials: "same-origin",

                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": csrfToken
                },

                body: JSON.stringify({})
            }
        );


        const data = await response.json();


        if (!response.ok) {

            showCartMessage(
                data.message ||
                "Unable to add product to cart."
            );

            return false;
        }


        /*
           Update cart badge using the value
           returned by Flask.
        */

        if (data.total_items !== undefined) {

            updateCartBadge(
                data.total_items
            );

        } else {

            updateCartBadge();
        }


        showCartMessage(
            data.message ||
            "Product added to your cart."
        );


        return true;


    } catch (error) {

        console.error(
            "Add to cart error:",
            error
        );


        showCartMessage(
            "Unable to add product to cart."
        );


        return false;
    }
}


/* =========================================
   UPDATE CART BADGE
   ========================================= */

function updateCartBadge(totalItems = null) {

    const badge =
        document.getElementById(
            "cartBadge"
        );


    if (!badge) {
        return;
    }


    /*
       If Flask returned the total number
       of cart items, use it.
    */

    if (totalItems !== null) {

        const total =
            Number(totalItems) || 0;


        badge.textContent =
            total;


        badge.style.display =
            total > 0
                ? "inline-flex"
                : "none";


        return;
    }


    /*
       Do NOT use localStorage.
       The cart is stored in the database.
    */

    badge.textContent = "0";

    badge.style.display = "none";
}


/* =========================================
   CART MESSAGE / TOAST
   ========================================= */

function showCartMessage(message) {

    const existing =
        document.querySelector(
            ".cart-toast"
        );


    if (existing) {
        existing.remove();
    }


    const toast =
        document.createElement(
            "div"
        );


    toast.className =
        "cart-toast";


    toast.innerHTML = `
        <i class="bi bi-check-circle"></i>
        <span>${message}</span>
    `;


    document.body.appendChild(
        toast
    );


    setTimeout(() => {

        if (
            toast &&
            toast.parentNode
        ) {
            toast.remove();
        }

    }, 2500);
}


/* =========================================
   UPDATE BADGE ON EVERY PAGE
   ========================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        updateCartBadge();

    }
);

function speakAIMessage() {
    if (!("speechSynthesis" in window)) return;

    const text = document.getElementById("aiVoiceText").dataset.message;

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);

    // Soft & polite speaking style
    utterance.rate = 0.88;
    utterance.pitch = 1.08;
    utterance.volume = 0.9;

    const voices = window.speechSynthesis.getVoices();

    // Prefer female English voices
    const femaleVoice = voices.find(voice =>
        /female|zira|samantha|aria|jenny|susan|hazel|google.*female/i.test(voice.name)
        && /en-IN|en-US|en-GB/i.test(voice.lang)
    );

    if (femaleVoice) {
        utterance.voice = femaleVoice;
    }

    window.speechSynthesis.speak(utterance);
}