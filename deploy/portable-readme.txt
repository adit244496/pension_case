Pension Case System - Retirement Gratuity (DCRG)
================================================

Running it
----------
Double-click  PensionCase.exe

A black window opens and says what it is doing, then the browser opens on the
case list. Leave that window open while you work; closing it closes the
application. There is no sign-in: the person at this machine is the operator.

If the browser does not open by itself, type the address the window shows -
usually  http://127.0.0.1:8000/  - into Edge or Chrome.


What this machine needs
-----------------------
* Windows 8.1, 10 or 11.
* Microsoft Word (any version from 2010). Word makes the PDFs. Without it the
  Word files are still produced, but not the PDFs.
* A browser: Edge or Chrome. Internet Explorer will not do.
* Nothing else. There is no Python or Node here, and nothing is installed -
  the folder can sit on the Desktop, or on a USB stick.

An internet connection is not needed at any point.


Your work
---------
Everything is in the  data  folder beside the .exe:

  data\pension.db     the cases
  data\storage        the Word files and PDFs
  data\templates      the forms, as your office has edited them

Back it up by copying that one folder. Moving the whole PensionCase folder to
another machine carries the cases with it.


Upgrading
---------
Copy the new PensionCase folder over the old one but keep your existing  data
folder. Any new forms are added to it; your edited wording is left alone.


If something goes wrong
-----------------------
The black window holds the message - read it before closing.

"Ports 8000-8003 and 8080 are all in use"
    Another copy is already running. Look for its window, or restart Windows.

"no Word found"
    Word is not installed, or is a version this cannot drive. Word files are
    still produced; open and print those, or use Save As PDF in Word.

Slow when producing a case
    Word is opened once per form. On an older machine the first case can take
    a few minutes. It is not stuck; the window keeps working.
