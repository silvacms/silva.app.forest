================
silva.app.forest
================

This extension provides you with the possibility to define advanced
virtual hosting strategies within `Silva`_.

To use this extension, you must add it to your `Silva`_ site, and
activate it in ``service_extension``. After, you will have a Silva
service available in ZMI, ``service_forest`` where you can define
virtual host, and rewrite rules inside each one.

To enable the extension you must click on activate in the
``service_forest``.

To trigger a virtual host, you must set the HTTP header ``X-VHM-Url``
inside your HTTP request to Silva.

This is done like this in Apache, for instance::

  <VirtualHost *:80>
    ServerName demo30.silvacms.org

    RequestHeader set X-VHM-URL http://demo30.silvacms.org
    RewriteEngine On
    RewriteRule ^/(.*)$ http://localhost:7778/$1 [P]
 </VirtualHost>


Credits
=======

Thanks to `WUW`_ for sponsoring this extension.

Code repository
===============

You can find the code of this extension in Git:
https://github.com/silvacms/silva.app.forest

.. _WUW: http://www.wu.ac.at/
.. _Silva: http://silvacms.org
