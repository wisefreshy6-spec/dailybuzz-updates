self.addEventListener("push", function (event) {
    let data = {};

    if (event.data) {
        data = event.data.json();
    }

    const title = data.title || "Daily Buzz Updates";
    const options = {
        body: data.body || "You have a new notification.",
        icon: "/static/images/icon-192.png",
        badge: "/static/images/icon-192.png",
        data: {
            url: data.url || "/dashboard/"
        }
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener("notificationclick", function (event) {
    event.notification.close();

    const targetUrl = event.notification.data.url || "/dashboard/";

    event.waitUntil(
        clients.matchAll({ type: "window", includeUncontrolled: true }).then(function (clientList) {
            for (const client of clientList) {
                if (client.url.includes(targetUrl) && "focus" in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});